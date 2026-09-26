import importlib.util
import os
import sys

import pytest

GUMRUK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gumruk_memuru")
sys.path.insert(0, GUMRUK)


@pytest.fixture(scope="session")
def chief():
    """Chief_1.2.py adindaki nokta yuzunden normal import edilemiyor."""
    spec = importlib.util.spec_from_file_location("chief_1_2", os.path.join(GUMRUK, "Chief_1.2.py"))
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul
