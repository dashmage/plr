import os
import pytest
import importlib

from plr import runner

@pytest.fixture()
def testrunner():
    test_module = importlib.import_module("tests.dummy_module")
    return runner.TestRunner(test_module)


def get_problems():
    os.chdir(os.path.join(os.getcwd(), "tests", "problems"))
    problems = []
    for file in os.listdir(os.getcwd()):
        if file == "__pycache__":
            continue
        problems.append(file.split("-", 1)[-1][:-3])
    return problems
    

@pytest.fixture(params=get_problems())
def problem(request):
    return request.param

