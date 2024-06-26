import re
from typing import Callable

from plr.show import (
    print_case_summary,
    print_dashes,
    print_heading,
    print_session_summary,
)

EVALUATE_FN_NAME = "evaluate"
VALIDATE_FN_NAME = "validate"


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
    def custom_evaluator(self) -> Callable | None:
        """Return custom evaluate function if defined in solution module."""
        global_attrs = list(vars(self.module))
        present = EVALUATE_FN_NAME if EVALUATE_FN_NAME in global_attrs else None
        if present:
            return getattr(self.module, EVALUATE_FN_NAME)
        return None

    @property
    def custom_validator(self) -> Callable | None:
        """Return custom validate function if defined in solution module."""
        global_attrs = list(vars(self.module))
        present = VALIDATE_FN_NAME if VALIDATE_FN_NAME in global_attrs else None
        if present:
            return getattr(self.module, VALIDATE_FN_NAME)
        return None

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
        """Convert string to a Python object for expected output."""
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

    def convert_string_to_dict(self, s):
        """Parse input kwargs as a dict from string.

        Eg:
        input:  "nums = [2,7,11,15], target = 9"
        result: {"nums": [2, 7, 11, 15], "target": 9}

        input:  "s='some string, with a comma'"
        result:
        """
        # ",\s*(?=\w+\s*=\s*)" regex explanation
        #   , matches the comma.
        #   \s* matches any whitespace characters (including none).
        #   (?=\w+\s*=\s*) is a lookahead assertion that checks for a sequence of word characters
        #   followed by optional whitespace around the equals sign.
        pairs = re.split(r",\s*(?=\w+\s*=\s*)", s)
        kwargs = {}
        for pair in pairs:
            key, value = pair.split("=")
            kwargs[key.strip()] = eval(value)
        return kwargs

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

    def run_tests(self):
        for method_name in self.solution_methods:
            print_heading(f"\n=== {method_name} ===\n")
            self.test_method(method_name)
