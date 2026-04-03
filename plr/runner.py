import ast
import inspect
import re
from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Optional, cast, get_args, get_origin

from plr.show import (
    print_case_summary,
    print_dashes,
    print_heading,
    print_session_summary,
)

PLACEHOLDER_VALUE = object()
EXAMPLE_RE = re.compile(
    r"^\s*Input:\s*(?P<input>.*?)^\s*Output:\s*(?P<output>.*?)(?=^\s*(?:Example(?:\s+\d+)?\s*:|Explanation\s*:|Constraints\s*:|Follow(?:-| )up\s*:|Note\s*:)|\Z)",
    flags=re.MULTILINE | re.DOTALL,
)


@dataclass(frozen=True)
class ExampleCase:
    input_text: str
    output_text: str


@dataclass(frozen=True)
class InPlacePrefixExpectation:
    result: Any
    target_name: str
    expected_prefix: list[Any]


def _unwrap_annotation(annotation):
    if annotation is inspect._empty:
        return None

    origin = get_origin(annotation)
    if origin is None:
        return annotation

    args = [arg for arg in get_args(annotation) if arg is not type(None)]
    if len(args) == 1:
        return _unwrap_annotation(args[0])
    return annotation


def _annotation_kind(annotation) -> Optional[str]:
    annotation = _unwrap_annotation(annotation)
    if annotation is None or not isinstance(annotation, type):
        return None

    if annotation.__name__ == "ListNode":
        return "linked_list"
    if annotation.__name__ == "TreeNode":
        return "tree"
    if annotation.__name__ == "Node":
        return "random_list"
    return None


def _build_linked_list(node_class, values):
    head = current = None
    for value in values:
        node = node_class(value)
        if head is None:
            head = current = node
        else:
            current = cast(Any, current)
            current.next = node
            current = node
    return head


def _serialize_linked_list(head):
    values = []
    while head is not None:
        values.append(head.val)
        head = head.next
    return values


def _build_tree(node_class, values):
    if not values:
        return None
    if values[0] is None:
        return None

    nodes = [None if value is None else node_class(value) for value in values]
    child_index = 1
    for node in nodes:
        if node is None:
            continue
        if child_index < len(nodes):
            node.left = nodes[child_index]
            child_index += 1
        if child_index < len(nodes):
            node.right = nodes[child_index]
            child_index += 1
    return nodes[0]


def _serialize_tree(root):
    if root is None:
        return []

    values = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            values.append(None)
            continue
        values.append(node.val)
        queue.append(node.left)
        queue.append(node.right)

    while values and values[-1] is None:
        values.pop()
    return values


def _build_random_list(node_class, values):
    if not values:
        return None

    nodes = [node_class(value[0]) for value in values]
    for index, (_, random_index) in enumerate(values):
        if index + 1 < len(nodes):
            nodes[index].next = nodes[index + 1]
        nodes[index].random = None if random_index is None else nodes[random_index]
    return nodes[0]


def _serialize_random_list(head):
    nodes = []
    indices = {}
    current = head
    while current is not None:
        indices[current] = len(nodes)
        nodes.append(current)
        current = current.next

    result = []
    for node in nodes:
        random_index = None if node.random is None else indices[node.random]
        result.append([node.val, random_index])
    return result


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


class TestRunner:
    def __init__(self, module):
        self.module = module
        self.solution = module.Solution() if hasattr(module, "Solution") else None
        self.doc = module.__doc__
        self.test_cases = self.parse_examples()

    @property
    def solution_methods(self) -> list:
        if self.solution is None:
            return []
        attrs = list(vars(self.solution.__class__))
        return [a for a in attrs if not a.startswith("_")]

    def parse_examples(self):
        if not self.doc:
            return []

        doc = dedent(self.doc).strip()
        matches = list(EXAMPLE_RE.finditer(doc))
        cases = []
        for index, match in enumerate(matches):
            output_text = _trim_output_block(match.group("output"))
            cases.append(
                ExampleCase(
                    input_text=dedent(match.group("input")).strip(),
                    output_text=output_text,
                )
            )
        return cases

    @staticmethod
    def eval_output(output: str):
        output_parts = _parse_output_parts(output)
        if len(output_parts) == 1 and output_parts[0][0] is None:
            return output_parts[0][1]
        return tuple(value for _, value in output_parts)

    def parse_input(self, s):
        if re.search(r"\b\w+\s*=", s):
            return self.convert_string_to_dict(s)

        parts = _split_top_level(_normalize_literals(s.strip()))
        return [_parse_literal(part) for part in parts]

    def convert_string_to_dict(self, s):
        expression = ast.parse(f"f({_normalize_literals(s.strip())})", mode="eval")
        call = cast(ast.Call, expression.body)
        return {
            kw.arg: _literal_from_node(kw.value)
            for kw in call.keywords
            if kw.arg is not None
        }

    def validate(self, actual, expected):
        if isinstance(expected, InPlacePrefixExpectation):
            if not isinstance(actual, tuple) or len(actual) != 2:
                return False
            actual_result, actual_prefix = actual
            if actual_result != expected.result:
                return False
            return actual_prefix == expected.expected_prefix

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

    def _adapt_value(self, annotation, value):
        kind = _annotation_kind(annotation)
        if kind == "linked_list" and isinstance(value, list):
            return _build_linked_list(_unwrap_annotation(annotation), value), kind
        if kind == "tree" and isinstance(value, list):
            return _build_tree(_unwrap_annotation(annotation), value), kind
        if kind == "random_list" and isinstance(value, list):
            return _build_random_list(_unwrap_annotation(annotation), value), kind
        return value, None

    def _serialize_value(self, value, kind):
        if kind == "linked_list":
            return _serialize_linked_list(value)
        if kind == "tree":
            return _serialize_tree(value)
        if kind == "random_list":
            return _serialize_random_list(value)
        return value

    def adapt_inputs(self, method, input_kwargs):
        signature = inspect.signature(method)
        adapted_kwargs = {}
        adapted_kinds = {}

        for name, value in input_kwargs.items():
            parameter = signature.parameters.get(name)
            annotation = parameter.annotation if parameter else inspect._empty
            adapted_value, kind = self._adapt_value(annotation, value)
            adapted_kwargs[name] = adapted_value
            if kind:
                adapted_kinds[name] = kind

        return adapted_kwargs, adapted_kinds

    def evaluate_actual(self, method, input_kwargs, expected):
        input_kwargs, adapted_kinds = self.adapt_inputs(method, input_kwargs)

        if isinstance(expected, InPlacePrefixExpectation):
            result = method(**input_kwargs)
            target_value = input_kwargs[expected.target_name]
            return result, target_value[:result]

        result = method(**input_kwargs)
        return_kind = _annotation_kind(inspect.signature(method).return_annotation)
        if return_kind:
            return self._serialize_value(result, return_kind)

        if result is None and len(adapted_kinds) == 1:
            target_name = next(iter(adapted_kinds))
            return self._serialize_value(input_kwargs[target_name], adapted_kinds[target_name])

        return result

    def test_design_problem(self):
        results = []
        for case in self.test_cases:
            operations, arguments = self.parse_input(case.input_text)
            expected = self.build_expected(case.output_text)
            class_name = operations[0]
            design_class = getattr(self.module, class_name)
            instance = None
            actual = []

            for operation, args in zip(operations, arguments):
                if operation == class_name:
                    instance = design_class(*args)
                    actual.append(None)
                    continue
                actual.append(getattr(instance, operation)(*args))

            is_success = self.validate(actual, expected)
            print_case_summary(case.input_text, actual, expected, is_success)
            results.append(is_success)
            print_dashes()

        print_session_summary(results)
        return all(results)

    def test_method(self, method_name):
        results = []
        for case in self.test_cases:
            input_kwargs = self.parse_input(case.input_text)
            expected = self.build_expected(case.output_text)
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
        if self.solution is None:
            print_heading("\n=== design ===\n")
            return self.test_design_problem()

        is_success = True
        for method_name in self.solution_methods:
            print_heading(f"\n=== {method_name} ===\n")
            is_success = self.test_method(method_name) and is_success
        return is_success
