import importlib
import importlib.util
import re
from pathlib import Path

from typer import Argument, Exit, Option, Typer, echo

from plr.fetcher import fetch_problem, make_gql_client
from plr.generator import create_content
from plr.runner import TestRunner

plr = Typer()


def load_problem_module(problem_path: str):
    candidate = Path(problem_path)
    if candidate.exists():
        module_path = candidate.resolve()
        module_name = re.sub(r"\W+", "_", module_path.stem)
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    module_name = problem_path.replace("/", ".").replace("\\", ".")
    return importlib.import_module(module_name)


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
    try:
        module = load_problem_module(problem_path)
    except (ImportError, FileNotFoundError, OSError) as exc:
        echo(f"Error while importing module: {exc}", err=True)
        raise Exit(code=1) from exc

    runner = TestRunner(module)
    if not runner.run_tests():
        raise Exit(code=1)
