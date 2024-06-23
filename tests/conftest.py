import os
import sys

import pytest

from plr import runner


@pytest.fixture()
def test_runner():
    sys.path.append(os.getcwd())
    test_module = __import__("dummy_module")
    return runner.TestRunner(test_module)
