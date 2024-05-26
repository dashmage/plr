import re
from typing import List, Optional

from plr.models import TestCase
from plr.show import (
    print_case_summary,
    print_dashes,
    print_heading,
    print_session_summary,
)


class Validator:
    def __init__(self, module):
        self.solution = module.Solution()
        self.doc = module.__doc__
        self.test_cases = self.parse_examples()
        self.check()

    @property
    def solution_methods(self) -> list:
        attrs = list(vars(self.solution.__class__))
        return [a for a in attrs if not a.startswith("_") and a != "test"]

    @property
    def custom_test_exists(self):
        attrs = list(vars(self.solution.__class__))
        return True if "test" in attrs else False

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

    def check(self, extra_cases: Optional[List[TestCase]] = None) -> List[bool]:
        extra_cases = extra_cases or []

        for method_name in self.solution_methods:
            results = []
            print_heading(f"\n=== {method_name} ===\n")
            for input_str, output_str in self.test_cases:
                expected = self.eval_output(output_str)

                method = getattr(self.solution, method_name)
                input_kwargs = self.parse_string_to_kwargs(input_str)
                if self.custom_test_exists:
                    test_method = getattr(self.solution, "test")
                    actual = test_method(method, input_kwargs)
                else:
                    actual = method(**input_kwargs)

                # actual = eval(f"self.solution.{method_name}({input_str})")

                print_case_summary(input_str, actual, expected)
                results.append(actual == expected)

                print_dashes()

            for test_case in extra_cases:
                print_dashes()
                method = getattr(self.solution, method_name)
                actual = method(*test_case.args.args, **test_case.args.kwargs)

                print_case_summary(test_case.args, actual, test_case.answer)
                results.append(actual == test_case.answer)

            print_session_summary(results)
        return results
