import ast
import re
from textwrap import dedent
from typing import Callable, Optional, cast

from plr.show import (
    print_case_summary,
    print_dashes,
    print_heading,
    print_session_summary,
)

EVALUATE_FN_NAME = "evaluate"
VALIDATE_FN_NAME = "validate"
PLACEHOLDER_VALUE = object()
EXAMPLE_RE = re.compile(
    r"^\s*Input:\s*(?P<input>.*?)^\s*Output:\s*(?P<output>.*?)(?=^\s*(?:Example(?:\s+\d+)?\s*:|Explanation\s*:|Constraints\s*:|Follow(?:-| )up\s*:|Note\s*:)|\Z)",
    flags=re.MULTILINE | re.DOTALL,
)


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


class TestRunner:
    def __init__(self, module):
        self.module = module
        self.solution = module.Solution()
        self.doc = module.__doc__
        self.test_cases = self.parse_examples()

    @property
    def solution_methods(self) -> list:
        """Return list of solution methods in the class as strings.

        Solution methods are all methods in the Solution class except for the
        custom validator method (if present).
        """
        attrs = list(vars(self.solution.__class__))
        return [a for a in attrs if not a.startswith("_")]

    @property
    def custom_evaluator(self) -> Optional[Callable]:
        """Return custom evaluate function if defined in solution module."""
        global_attrs = list(vars(self.module))
        present = EVALUATE_FN_NAME if EVALUATE_FN_NAME in global_attrs else None
        if present:
            return getattr(self.module, EVALUATE_FN_NAME)
        return None

    @property
    def custom_validator(self) -> Optional[Callable]:
        """Return custom validate function if defined in solution module."""
        global_attrs = list(vars(self.module))
        present = VALIDATE_FN_NAME if VALIDATE_FN_NAME in global_attrs else None
        if present:
            return getattr(self.module, VALIDATE_FN_NAME)
        return None

    def parse_examples(self):
        if not self.doc:
            return []

        doc = dedent(self.doc).strip()
        return [
            [
                dedent(match.group("input")).strip(),
                _trim_output_block(match.group("output")),
            ]
            for match in EXAMPLE_RE.finditer(doc)
        ]

    @staticmethod
    def eval_output(output: str):
        """Convert string to a Python object for expected output."""
        output_elements = _split_top_level(output)
        if len(output_elements) == 1:
            return _parse_literal(output_elements[0])

        result = []
        for element in output_elements:
            key, separator, value = element.partition("=")
            result.append(_parse_literal(value if separator else key))
        return tuple(result)

    def convert_string_to_dict(self, s):
        """Parse input kwargs as a dict from string.

        Eg:
        input:  "nums = [2,7,11,15], target = 9"
        result: {"nums": [2, 7, 11, 15], "target": 9}

        input:  "s='some string, with a comma'"
        result:
        """
        expression = ast.parse(f"f({ _normalize_literals(s.strip()) })", mode="eval")
        call = cast(ast.Call, expression.body)
        return {
            kw.arg: _literal_from_node(kw.value)
            for kw in call.keywords
            if kw.arg is not None
        }

    def validate(self, actual, expected, custom_validator=None):
        is_success = None
        if custom_validator:
            is_success = True if custom_validator(actual, expected) else False
        else:
            is_success = True if actual == expected else False
        return is_success

    def test_method(self, method_name):
        results = []
        for input_str, output_str in self.test_cases:
            input_kwargs = self.convert_string_to_dict(input_str)
            expected = self.eval_output(output_str)
            solution_method = getattr(self.solution, method_name)

            if self.custom_evaluator:
                actual = self.custom_evaluator(solution_method, input_kwargs)
            else:
                # if there's multiple elements expected in the output, then
                # there's in-place changes on the input and the solution method
                # should have a custom evaluator
                if isinstance(expected, tuple):
                    print(
                        "Multiple output elements detected but no custom evaluator...exiting"
                    )
                    exit()
                actual = solution_method(**input_kwargs)

            is_success = (
                self.validate(actual, expected, self.custom_validator)
                if self.custom_validator
                else self.validate(actual, expected)
            )

            print_case_summary(input_str, actual, expected, is_success)
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
