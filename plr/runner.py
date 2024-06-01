import re
from typing import Callable, List, Optional

from plr.models import TestCase
from plr.show import (
    print_case_summary,
    print_dashes,
    print_heading,
    print_session_summary,
)


class TestValidator:
    def __init__(self, module):
        self.solution = module.Solution()
        self.doc = module.__doc__
        self.test_cases = self.parse_examples()
        self.validate()

    @property
    def solution_methods(self) -> list:
        """Return list of solution methods in the class as strings.

        Solution methods are all methods in the Solution class except for the
        custom validator method (if present).
        """
        attrs = list(vars(self.solution.__class__))
        return [a for a in attrs if not a.startswith("_")]

    def parse_examples(self):
        examples = []
        for example in self.doc.split("xampl"):
            match = re.search(
                r"Input:(?P<input>.*)?$\nOutput:(?P<output>.*)?$",
                example,
                flags=re.MULTILINE,
            )
            if match:
                input_str = match.group("input").strip()
                output_str = match.group("output").strip()
                examples.append([input_str, output_str])

        return examples

    @staticmethod
    def eval_output(output: str):
        if output.lower() == "false":
            return False
        if output.lower() == "true":
            return True
        # when dealing with in-place change questions with two output elements
        # eg: if output = "2, nums=[1,2,_]"
        # result = (2, [1, 2])
        result = ()
        if len(output_elements := output.split(", ")) > 1:
            for element in output_elements:
                if "=" in element:
                    value = element.split("=")[1].replace(",_", "")
                    result = result + (eval(value),)
                else:
                    result = result + (eval(element),)
        else:
            result = eval(output)
        return result

    def parse_string_to_kwargs(self, s):
        # assuming each pair of kwargs are separated by ", "
        # and any list, set, dict doesn't have space after the comma
        pairs = s.split(", ")
        kwargs = {}
        for pair in pairs:
            key, value = pair.split("=")
            kwargs[key.strip()] = eval(value)
        return kwargs

    def advanced_validator(self, method: Callable, input_args: dict):
        """Advanced validator for dealing with multiple output elements."""
        result = method(**input_args)
        return result, input_args["nums"][:result]

    def validate(self, extra_cases: Optional[List[TestCase]] = None) -> List[bool]:
        extra_cases = extra_cases or []

        for method_name in self.solution_methods:
            results = []
            print_heading(f"\n=== {method_name} ===\n")
            for input_str, output_str in self.test_cases:
                expected = self.eval_output(output_str)

                solution_method = getattr(self.solution, method_name)
                input_kwargs = self.parse_string_to_kwargs(input_str)

                # questions requiring in-place changes with multiple
                # output elements requires more complex validation
                if isinstance(expected, tuple):
                    actual = self.advanced_validator(solution_method, input_kwargs)
                    print_case_summary(input_str, actual, expected)
                else:
                    actual = solution_method(**input_kwargs)
                    print_case_summary(input_str, actual, expected)

                results.append(actual == expected)

                print_dashes()

            for test_case in extra_cases:
                print_dashes()
                solution_method = getattr(self.solution, method_name)
                actual = solution_method(*test_case.args.args, **test_case.args.kwargs)

                print_case_summary(test_case.args, actual, test_case.answer)
                results.append(actual == test_case.answer)

            print_session_summary(results)
        return results
