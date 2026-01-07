import os
import sys
from pathlib import Path

from typer import Argument, Option, Typer, echo

from plr.fetcher import fetch_problem, make_gql_client
from plr.generator import create_content
from plr.runner import TestRunner

plr = Typer()


@plr.command()
def pull(
    slug: str = Argument(..., help="Problem slug"),
    out: Path = Option(
        None, help="Output filename. Defaults to $id-$slug.py in the current folder"
    ),
):
    """Pull down provided problem from LeetCode."""
    client = make_gql_client()
    problem = fetch_problem(client, slug)
    content = create_content(problem)

    if not out:
        out = Path(f"{problem.question.question_id}-{slug}.py")

    out.write_text(content, encoding="utf8")
    echo(f"{out} has been created! Happy solving")


@plr.command()
def test(problem_path: str = Argument(..., help="Path to problem file")):
    """Run the tests for the provided path to problem."""
    if problem_path is None:
        print("Path to problem not provided.")
        exit()

    module_name = problem_path.replace("/", ".").rstrip(".py")
    sys.path.append(os.getcwd())
    try:
        module = __import__(module_name, fromlist=["*"])
    except ModuleNotFoundError:
        print(f"Error while importing module: {module_name}")
        exit()

    runner = TestRunner(module)
    runner.run_tests()
