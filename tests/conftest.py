import importlib
from pathlib import Path

import pytest

from plr import runner

PROBLEMS_DIR = Path(__file__).parent / "problems"


@pytest.fixture()
def testrunner():
    test_module = importlib.import_module("tests.dummy_module")
    return runner.TestRunner(test_module)


def get_problems():
    return sorted(path for path in PROBLEMS_DIR.glob("*.py"))


@pytest.fixture(params=get_problems())
def problem(request):
    return request.param
