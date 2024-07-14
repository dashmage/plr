import os
import pytest
import subprocess

# TODO: Add tests
# For custom validator usage
# For plr pull functionality

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
    [("false", False), ("true", True), ("2, nums=[1,2,_]", (2, [1, 2]))],
)
def test_eval_output(testrunner, output, expected):
    assert testrunner.eval_output(output) == expected


def test_validate(testrunner):
    actual = [1, 2, 3]
    expected = [1, 2, 3]
    assert testrunner.validate(actual, expected) is True


@pytest.mark.parametrize(
    "s,expected",
    [
        ("nums = [1,2,3], target = 9", {"nums": [1, 2, 3], "target": 9}),
        ("teststr = 'a string, with a comma'", {"teststr": "a string, with a comma"})
    ],
)
def test_convert_string_to_dict(testrunner, s, expected):
    assert testrunner.convert_string_to_dict(s) == expected


def test_problems(problem):
    # fetch problems one at a time from problems/
    # run plr test on each of them
    # check whether all tests are successful
    result = subprocess.run(f"plr test {problem}".split(), capture_output=True, text=True)
    if "FAILED" in result.stdout:
        assert False, f"Failed problem {problem}.\n{result.stdout}"
    print(f"{problem} passed.")
