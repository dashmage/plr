import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from plr.cli import load_problem_module
from plr.generator import render_python_snippet
from plr import runner as runner_module

PROBLEMS_DIR = Path(__file__).parent / "problems"


def test_solution_methods(testrunner):
    assert testrunner.solution_methods == ["dummy_solution1", "dummy_solution2"]


def test_custom_evaluator(testrunner):
    assert testrunner.custom_evaluator() == "custom evaluator present"


def test_custom_validator(testrunner):
    assert testrunner.custom_validator() == "custom validator present"


def test_parse_examples(testrunner):
    parsed_result = testrunner.parse_examples()
    expected_results = [
        ["nums = [2,7,11,15], target = 9", "[0,1]"],
        ["nums = [3,2,2,3], val = 3", "2, nums = [2,2,_,_]"],
    ]
    assert parsed_result == expected_results


@pytest.mark.parametrize(
    "output,expected",
    [
        ("false", False),
        ("true", True),
        ("2, nums=[1,2,_]", (2, [1, 2])),
        ("[\n  [1, 2],\n  [3, 4]\n]", [[1, 2], [3, 4]]),
    ],
)
def test_eval_output(testrunner, output, expected):
    assert testrunner.eval_output(output) == expected


def test_eval_output_rejects_calls(testrunner):
    with pytest.raises(ValueError):
        testrunner.eval_output("__import__('os').system('echo unsafe')")


def test_validate(testrunner):
    actual = [1, 2, 3]
    expected = [1, 2, 3]
    assert testrunner.validate(actual, expected) is True


@pytest.mark.parametrize(
    "s,expected",
    [
        ("nums = [1,2,3], target = 9", {"nums": [1, 2, 3], "target": 9}),
        ("teststr = 'a string, with a comma'", {"teststr": "a string, with a comma"}),
        (
            "head = [1,2,3], active = true, tail = null",
            {"head": [1, 2, 3], "active": True, "tail": None},
        ),
        (
            "grid = [[1,2],[3,4]],\nlabel = 'matrix'",
            {"grid": [[1, 2], [3, 4]], "label": "matrix"},
        ),
    ],
)
def test_convert_string_to_dict(testrunner, s, expected):
    assert testrunner.convert_string_to_dict(s) == expected


def test_parse_examples_multiline():
    module = ModuleType("multiline_examples")
    module.__doc__ = """
    Example 1:
    Input:
    grid = [[1, 2], [3, 4]],
    active = true
    Output:
    [
      [1, 2],
      [3, 4]
    ]
    Explanation: Multiline input and output should both parse.

    Example 2:
    Input: head = [1,2,3]
    Output: null
    """

    class Solution:
        def solve(self):
            return None

    setattr(module, "Solution", Solution)
    runner = runner_module.TestRunner(module)
    assert runner.parse_examples() == [
        ["grid = [[1, 2], [3, 4]],\nactive = true", "[\n  [1, 2],\n  [3, 4]\n]"],
        ["head = [1,2,3]", "null"],
    ]


def test_load_problem_module_from_file():
    module = load_problem_module(str(PROBLEMS_DIR / "1-two-sum.py"))
    assert module.Solution().twoSum([2, 7, 11, 15], 9) == [0, 1]


def test_render_python_snippet_adds_pass_for_stub():
    code = "class Solution:\n    def solve(self):\n        "
    assert render_python_snippet(code).endswith("        pass\n")


def test_render_python_snippet_preserves_existing_body():
    code = "class Solution:\n    def solve(self):\n        return 1\n"
    assert render_python_snippet(code) == code


def test_problems(problem):
    result = subprocess.run(
        [sys.executable, "-m", "plr", "test", str(problem)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "FAILED" not in result.stdout, f"Failed problem {problem}.\n{result.stdout}"
