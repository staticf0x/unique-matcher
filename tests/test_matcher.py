import os
import pathlib
import sys

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


def _load_data(folder: pathlib.Path) -> list[str]:
    data = []

    for item in os.listdir(folder):
        screenshots = [folder / item / file for file in os.listdir(folder / item)]
        data.append((item, screenshots))

    return data


CONTAINS = _load_data(DATA_DIR / "contains")
CONTAINS_NOT = _load_data(DATA_DIR / "contains_not")


@pytest.mark.parametrize(["name", "screenshots"], CONTAINS)
def test_find_item_contains_item(name, screenshots, matcher):
    for screenshot in screenshots:
        result = matcher.find_item(screenshot)
        assert result.item.file == name


@pytest.mark.parametrize(["name", "screenshots"], CONTAINS_NOT)
def test_find_item_doesnt_contain_item(name, screenshots, matcher):
    for screenshot in screenshots:
        result = matcher.find_item(screenshot)
        assert result.item.file != name
