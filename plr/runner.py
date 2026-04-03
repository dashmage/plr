import ast
import re
from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Optional, cast

from plr.show import (
    print_case_summary,
    print_dashes,
    print_heading,
    print_session_summary,
)

PLACEHOLDER_VALUE = object()
DEFAULT_COMPARE_MODE = "exact"
UNORDERED_COMPARE_MODE = "unordered"
NESTED_UNORDERED_COMPARE_MODE = "nested-unordered"
INPLACE_PREFIX_COMPARE_MODE = "inplace-prefix"
INPLACE_PREFIX_UNORDERED_COMPARE_MODE = "inplace-prefix-unordered"
EXAMPLE_RE = re.compile(
    r"^\s*Input:\s*(?P<input>.*?)^\s*Output:\s*(?P<output>.*?)(?=^\s*(?:Example(?:\s+\d+)?\s*:|Explanation\s*:|Constraints\s*:|Follow(?:-| )up\s*:|Note\s*:)|\Z)",
    flags=re.MULTILINE | re.DOTALL,
)
ANY_ORDER_RE = re.compile(
    r"\bany order\b|order of the output.*does not matter|order of the triplets.*does not matter|can be returned in any order",
    flags=re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class ExampleCase:
    input_text: str
    output_text: str
    compare_mode: str = DEFAULT_COMPARE_MODE


@dataclass(frozen=True)
class InPlacePrefixExpectation:
    result: Any
    target_name: str
    expected_prefix: list[Any]


def _normalize_literals(raw: str) -> str:
    return re.sub(
        r"\b(true|false|null)\b",
        lambda match: {
            "true": "True",
            "false": "False",
            "null": "None",
        }[match.group(1)],
        raw,
        flags=re.IGNORECASE,
    )


def _split_top_level(raw: str) -> list[str]:
    parts = []
    start = 0
    depth = 0
    quote = None
    escaped = False

    for index, char in enumerate(raw):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            quote = char
            continue

        if char in "([{":
            depth += 1
            continue
        if char in ")]}":
            depth -= 1
            continue

        if depth == 0 and char in {",", "\n"}:
            part = raw[start:index].strip()
            if part:
                parts.append(part)
            start = index + 1

    tail = raw[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _literal_from_node(node: ast.AST):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in {"True", "False", "None"}:
            return ast.literal_eval(node)
        if node.id == "_":
            return PLACEHOLDER_VALUE
    if isinstance(node, ast.List):
        return [
            value
            for child in node.elts
            if (value := _literal_from_node(child)) is not PLACEHOLDER_VALUE
        ]
    if isinstance(node, ast.Tuple):
        return tuple(
            value
            for child in node.elts
            if (value := _literal_from_node(child)) is not PLACEHOLDER_VALUE
        )
    if isinstance(node, ast.Set):
        return {
            value
            for child in node.elts
            if (value := _literal_from_node(child)) is not PLACEHOLDER_VALUE
        }
    if isinstance(node, ast.Dict):
        result = {}
        for key_node, value_node in zip(node.keys, node.values):
            key = _literal_from_node(key_node)
            value = _literal_from_node(value_node)
            if value is not PLACEHOLDER_VALUE:
                result[key] = value
        return result
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _literal_from_node(node.operand)
        return operand if isinstance(node.op, ast.UAdd) else -operand
    raise ValueError("Unsupported literal in example")


def _parse_literal(raw: str):
    expression = ast.parse(_normalize_literals(raw.strip()), mode="eval")
    return _literal_from_node(expression.body)


def _parse_output_parts(output: str) -> list[tuple[Optional[str], Any]]:
    parts = []
    for element in _split_top_level(output):
        key, separator, value = element.partition("=")
        parts.append((key.strip() if separator else None, _parse_literal(value if separator else key)))
    return parts


def _is_complete_output(raw: str) -> bool:
    candidate = raw.strip()
    if not candidate or candidate.endswith(","):
        return False
    try:
        TestRunner.eval_output(candidate)
    except (SyntaxError, ValueError):
        return False
    return True


def _trim_output_block(raw: str) -> str:
    lines = dedent(raw).strip().splitlines()
    output_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if output_lines and _is_complete_output("\n".join(output_lines)):
                break
            continue

        if output_lines and _is_complete_output("\n".join(output_lines)):
            if re.match(
                r"^(?:Explanation|Constraints|Follow(?:-| )up|Note)\s*:",
                stripped,
            ):
                break
            break

        output_lines.append(line)

    return "\n".join(output_lines).strip()


def _normalize_unordered(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(
            sorted(
                (_normalize_unordered(key), _normalize_unordered(item))
                for key, item in value.items()
            )
        )
    if isinstance(value, (list, tuple)):
        normalized_items = [_normalize_unordered(item) for item in value]
        return tuple(sorted(normalized_items, key=repr))
    if isinstance(value, set):
        return tuple(sorted((_normalize_unordered(item) for item in value), key=repr))
    return value


def _contains_nested_sequence(value: Any) -> bool:
    return isinstance(value, (list, tuple)) and any(
        isinstance(item, (list, tuple, set, dict)) for item in value
    )


class TestRunner:
    def __init__(self, module):
        self.module = module
        self.solution = module.Solution()
        self.doc = module.__doc__
        self.active_compare_mode = DEFAULT_COMPARE_MODE
        self.test_cases = self.parse_examples()

    @property
    def solution_methods(self) -> list:
        attrs = list(vars(self.solution.__class__))
        return [a for a in attrs if not a.startswith("_")]

    def parse_examples(self):
        if not self.doc:
            return []

        doc = dedent(self.doc).strip()
        matches = list(EXAMPLE_RE.finditer(doc))
        cases = []
        for index, match in enumerate(matches):
            next_start = matches[index + 1].start() if index + 1 < len(matches) else len(doc)
            context = doc[match.start() : next_start]
            output_text = _trim_output_block(match.group("output"))
            compare_mode = self.infer_compare_mode(output_text, context, doc)
            cases.append(
                ExampleCase(
                    input_text=dedent(match.group("input")).strip(),
                    output_text=output_text,
                    compare_mode=compare_mode,
                )
            )
        return cases

    @staticmethod
    def eval_output(output: str):
        output_parts = _parse_output_parts(output)
        if len(output_parts) == 1 and output_parts[0][0] is None:
            return output_parts[0][1]
        return tuple(value for _, value in output_parts)

    def convert_string_to_dict(self, s):
        expression = ast.parse(f"f({_normalize_literals(s.strip())})", mode="eval")
        call = cast(ast.Call, expression.body)
        return {
            kw.arg: _literal_from_node(kw.value)
            for kw in call.keywords
            if kw.arg is not None
        }

    def infer_compare_mode(self, output_text: str, context: str, full_doc: str) -> str:
        output_parts = _parse_output_parts(output_text)
        is_inplace_prefix = (
            len(output_parts) == 2
            and output_parts[0][0] is None
            and output_parts[1][0] is not None
            and isinstance(output_parts[1][1], list)
        )
        expected = self.eval_output(output_text)
        signals = "\n".join([context, full_doc])
        mentions_any_order = bool(ANY_ORDER_RE.search(signals))
        mentions_sorting_judge = "sort(nums, 0, k)" in full_doc.lower()

        if is_inplace_prefix:
            if mentions_any_order or mentions_sorting_judge:
                return INPLACE_PREFIX_UNORDERED_COMPARE_MODE
            return INPLACE_PREFIX_COMPARE_MODE

        if mentions_any_order:
            if _contains_nested_sequence(expected):
                return NESTED_UNORDERED_COMPARE_MODE
            return UNORDERED_COMPARE_MODE

        return DEFAULT_COMPARE_MODE

    def validate(self, actual, expected):
        if isinstance(expected, InPlacePrefixExpectation):
            if not isinstance(actual, tuple) or len(actual) != 2:
                return False
            actual_result, actual_prefix = actual
            if actual_result != expected.result:
                return False
            if self.active_compare_mode == INPLACE_PREFIX_UNORDERED_COMPARE_MODE:
                return _normalize_unordered(actual_prefix) == _normalize_unordered(
                    expected.expected_prefix
                )
            return actual_prefix == expected.expected_prefix

        if self.active_compare_mode in {
            UNORDERED_COMPARE_MODE,
            NESTED_UNORDERED_COMPARE_MODE,
        }:
            return _normalize_unordered(actual) == _normalize_unordered(expected)

        return actual == expected

    def build_expected(self, output_text: str):
        output_parts = _parse_output_parts(output_text)
        if (
            len(output_parts) == 2
            and output_parts[0][0] is None
            and output_parts[1][0] is not None
            and isinstance(output_parts[1][1], list)
        ):
            return InPlacePrefixExpectation(
                result=output_parts[0][1],
                target_name=output_parts[1][0],
                expected_prefix=cast(list[Any], output_parts[1][1]),
            )
        return self.eval_output(output_text)

    def evaluate_actual(self, method, input_kwargs, expected):
        if isinstance(expected, InPlacePrefixExpectation):
            result = method(**input_kwargs)
            target_value = input_kwargs[expected.target_name]
            return result, target_value[:result]
        return method(**input_kwargs)

    def test_method(self, method_name):
        results = []
        for case in self.test_cases:
            input_kwargs = self.convert_string_to_dict(case.input_text)
            expected = self.build_expected(case.output_text)
            self.active_compare_mode = case.compare_mode
            solution_method = getattr(self.solution, method_name)
            actual = self.evaluate_actual(solution_method, input_kwargs, expected)

            is_success = self.validate(actual, expected)
            expected_display = (
                (expected.result, expected.expected_prefix)
                if isinstance(expected, InPlacePrefixExpectation)
                else expected
            )
            print_case_summary(case.input_text, actual, expected_display, is_success)
            results.append(is_success)
            print_dashes()

        print_session_summary(results)
        return all(results)

    def run_tests(self):
        is_success = True
        for method_name in self.solution_methods:
            print_heading(f"\n=== {method_name} ===\n")
            is_success = self.test_method(method_name) and is_success
        return is_success
