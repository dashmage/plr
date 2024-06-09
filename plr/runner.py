import re
from typing import Callable, List, Optional

from plr.models import TestCase
from plr.show import (
    print_case_summary,
    print_dashes,
    print_heading,
    print_session_summary,
)

CUSTOM_EVAL_FN = "evaluate"

class TestValidator:
    def __init__(self, module):
        self.module = module
        self.solution = module.Solution()
        self.doc = module.__doc__
        self.test_cases = self.parse_examples()
        self.run_tests()

    @property
    def solution_methods(self) -> list:
        """Return list of solution methods in the class as strings.

        Solution methods are all methods in the Solution class except for the
        custom validator method (if present).
        """
        attrs = list(vars(self.solution.__class__))
        return [a for a in attrs if not a.startswith("_")]

    @property
    def custom_evaluator(self) -> str | None:
        """Check if evaluate function has been defined in solution module.
        
        evaluate function: evaluates result of solution method in non-standard case.
        """
        global_attrs = list(vars(self.module))
        return CUSTOM_EVAL_FN if CUSTOM_EVAL_FN in global_attrs else None

    @property
    def custom_validator(self) -> str | None:
        """Check if evaluate function has been defined in solution module.
        
        evaluate function: evaluates result of solution method in non-standard case.
        """
        global_attrs = list(vars(self.module))
        return "validate" if "validate" in global_attrs else None

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
        """Parse input kwargs from string.

        Eg: TODO
        """
        # , matches the comma.
        # \s* matches any whitespace characters (including none).
        # (?=\w+\s*=\s*) is a lookahead assertion that checks for a sequence of word characters
        #  followed by optional whitespace around the equals sign.
        pairs = re.split(r',\s*(?=\w+\s*=\s*)', s)
        kwargs = {}
        for pair in pairs:
            key, value = pair.split("=")
            kwargs[key.strip()] = eval(value)
        return kwargs

    def advanced_validator(self, method: Callable, input_args: dict):
        """Advanced validator for dealing with multiple output elements."""
        result = method(**input_args)
        return result, input_args["nums"][:result]

    def run_tests(self, extra_cases: Optional[List[TestCase]] = None) -> List[bool]:
        extra_cases = extra_cases or []

        for method_name in self.solution_methods:
            results = []
            print_heading(f"\n=== {method_name} ===\n")
            for input_str, output_str in self.test_cases:
                expected = self.eval_output(output_str)

                solution_method = getattr(self.solution, method_name)
                input_kwargs = self.parse_string_to_kwargs(input_str)

                if self.custom_evaluator:
                    custom_evaluator = getattr(self.module, self.custom_evaluator)
                    actual = custom_evaluator(solution_method, input_kwargs)
                else:
                    if isinstance(expected, tuple):
                        # multiple output elements but no custom validator
                        print("multiple output elements detected, provide custom evaluator function")
                        exit()
                    actual = solution_method(**input_kwargs)

                if self.custom_validator:
                    custom_validator = getattr(self.module, self.custom_validator)
                    test_output = print_case_summary(input_str, actual, expected, custom_validator=custom_validator)
                    results.append(test_output)
                else:
                    test_output = print_case_summary(input_str, actual, expected)
                    results.append(test_output)

                print_dashes()

            for test_case in extra_cases:
                print_dashes()
                solution_method = getattr(self.solution, method_name)
                actual = solution_method(*test_case.args.args, **test_case.args.kwargs)

                print_case_summary(test_case.args, actual, test_case.answer)
                results.append(actual == test_case.answer)

            print_session_summary(results)
        return results

