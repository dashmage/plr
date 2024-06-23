import os
import sys
from pathlib import Path

from typer import Argument, Option, Typer, echo

from plr.fetcher import fetch_problem, make_gql_client
from plr.generator import create_content
from plr.runner import TestValidator

plr = Typer()


@plr.command()
def pull(
    slug: str = Argument(..., help="Problem slug"),
    out: Path = Option(
        None, help="Output filename. Defaults to $id-$slug.py in the current folder"
    ),
):
    client = make_gql_client()
    problem = fetch_problem(client, slug)
    content = create_content(problem)

    if not out:
        out = Path(f"{problem.question.question_id}-{slug}.py")

    out.write_text(content, encoding="utf8")
    echo(f"{out} has been created! Happy solving")


@plr.command()
def test(slug: str = Argument(..., help="Problem slug")):
    """Run the tests for the provided problem slug."""
    module_name = None
    for file in os.listdir(os.getcwd()):
        # strip problem id and .py suffix, then compare with slug
        if file.split("-", 1)[-1][:-3] == slug:
            module_name = file[:-3]  # remove .py suffix
    if module_name is None:
        print("Error: Not able to find file")
        exit()
    sys.path.append(os.getcwd())
    try:
        module = __import__(module_name)
    except ModuleNotFoundError:
        print(f"Error while importing module: {module_name}")
        exit()

    val = TestValidator(module)
    val.run_tests()
