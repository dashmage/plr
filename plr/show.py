from typing import List

from rich import print as rprint


def print_green(text: str):
    rprint(f"[green]{text}[/green]")


def print_red(text: str):
    rprint(f"[red]{text}[/red]")


def print_dashes():
    print("-" * 30)


def print_heading(text: str):
    rprint(f"[bright_blue]{text}[/bright_blue]")


def print_case_summary(args, actual, expected, is_success):
    print_green("[ OK ]") if is_success else print_red("[ FAILED ]")
    print(args)
    print("Expected:", expected)
    print("Actual  :", actual)


def print_session_summary(results: List[bool]):
    passed = sum(x for x in results if x)
    total = len(results)
    p = print_green if passed == total else print_red
    p(f"\nPassed: {passed}/{total}")
