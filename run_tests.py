"""Helper script to run test_find_item_contains_item on a selected data set."""
import os

import pytest
from simple_term_menu import TerminalMenu  # type: ignore[import]

from unique_matcher.constants import ROOT_DIR

DATA_DIR = ROOT_DIR / "tests" / "test_data" / "contains"

data_sets = [*sorted(os.listdir(DATA_DIR)), "all"]

# Make the user choose a data set
menu = TerminalMenu(data_sets)
choice_idx = menu.show()

os.environ["DATA_SET"] = data_sets[choice_idx]
pytest.main(["-n", "auto", "-v", "tests/test_matcher.py::test_find_item_contains_item"])
