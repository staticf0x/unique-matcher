import os
import pathlib
import sys

from pathlib import Path

import pytest
from loguru import logger

DATA_DIR = pathlib.Path(__file__).parent / "test_data"

# Enable logging by running pytest with the `-s` switch
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | <level>{level:7s}</level> | {message}",
    level="DEBUG",
    colorize=True,
)


def _load_data(folder: pathlib.Path) -> list[tuple[str, list[Path]]]:
    data = []

    for item in sorted(os.listdir(folder)):
        screenshots = [folder / item / file for file in os.listdir(folder / item)]
        data.append((item, screenshots))

    return data


TEST_SET = os.getenv("DATA_SET", "example")

if TEST_SET == "all":
    CONTAINS = [
        sublist
        for data_set in os.listdir(DATA_DIR / "contains")
        for sublist in _load_data(DATA_DIR / "contains" / data_set)
    ]
else:
    CONTAINS = _load_data(DATA_DIR / "contains" / TEST_SET)

CONTAINS_NOT = _load_data(DATA_DIR / "contains_not")
BASES = _load_data(DATA_DIR / "bases")


@pytest.mark.parametrize(("name", "screenshots"), CONTAINS)
def test_find_item_contains_item(name, screenshots, matcher):
    """Test that a screenshot contains a specified item."""
    for screenshot in screenshots:
        result = matcher.find_item(screenshot)
        assert result.item.file == name


@pytest.mark.parametrize(("name", "screenshots"), CONTAINS_NOT)
def test_find_item_doesnt_contain_item(name, screenshots, matcher):
    """Test that a screenshot does NOT contain a specified item."""
    # TODO: Can we just invert the CONTAINS data set?
    for screenshot in screenshots:
        result = matcher.find_item(screenshot)
        assert result.item.file != name


@pytest.mark.parametrize(("base", "screenshots"), BASES)
def test_get_base_name(base, screenshots, matcher):
    for screenshot in screenshots:
        cropped_item = matcher.find_unique(screenshot)
        assert cropped_item.base == base
