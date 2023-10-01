from unittest.mock import patch

import pytest

from unique_matcher.constants import TESSERACT_PATH
from unique_matcher.matcher.items import ItemLoader
from unique_matcher.matcher.title import TitleParser, pytesseract


@pytest.fixture(scope="session")
def parser():
    item_loader = ItemLoader()
    item_loader.load()

    return TitleParser(item_loader)


@patch("pathlib.Path.exists", return_value=True)
@patch("sys.platform", "win32")
def test_tesseract_windows_exists(_):
    # Reset to default to avoid tests depending on each other
    pytesseract.pytesseract.tesseract_cmd = "tesseract"

    item_loader = ItemLoader()
    item_loader.load()

    _ = TitleParser(item_loader)
    assert pytesseract.pytesseract.tesseract_cmd == TESSERACT_PATH


@patch("sys.platform", "win32")
def test_tesseract_windows_path():
    # Reset to default to avoid tests depending on each other
    pytesseract.pytesseract.tesseract_cmd = "tesseract"

    item_loader = ItemLoader()
    item_loader.load()

    _ = TitleParser(item_loader)
    assert pytesseract.pytesseract.tesseract_cmd == "tesseract"


def test_clean_title(parser: TitleParser):
    assert parser._clean_title("BLOODBOUND\nBONE ARMOUR\n\n") == "BLOODBOUND\nBONE ARMOUR\n\n"
    assert parser._clean_title("IMPERIAL STAFF\n\n") == "IMPERIAL STAFF\n\n"
    assert (
        parser._clean_title("BONES OF ULLR\nSILK SLIPPERS\n\n")
        == "BONES OF ULLR\nSILK SLIPPERS\n\n"
    )
    assert parser._clean_title("SILK SLIPPERS\n\n") == "SILK SLIPPERS\n\n"

    # Apostrophe
    assert (
        parser._clean_title("BEREK’S GRIP\nTWO-STONE RING\n\n")  # noqa: RUF001
        == "BEREKS GRIP\nTWO-STONE RING\n\n"
    )

    # Incorrect possessive
    assert (
        parser._clean_title("BEREK S GRIP\nTWO-STONE RING\n\n") == "BEREKS GRIP\nTWO-STONE RING\n\n"
    )

    # One word base
    assert parser._clean_title("LATHI\n\n") == "LATHI\n\n"

    # Random 2 letter word in there
    assert parser._clean_title("TWO-STONE NE RING\n\n") == "TWO-STONE RING\n\n"


def test_find_item_name(parser):
    """Trying to find the item name in the parsed title."""
    # Typical name
    assert parser._find_item_name(["BEREKS GRIP", "TWO-STONE RING"]) == "Bereks_Grip"

    # Including "of, the"
    assert (
        parser._find_item_name(["PILLAR OF THE CAGED GOD", "IRON STAFF"])
        == "Pillar_of_the_Caged_God"
    )

    # Including a dash
    assert parser._find_item_name(["THREE-STEP ASSAULT", "SHAGREEN BOOTS"]) == "Three-step_Assault"


def test_find_item_name_no_item(parser):
    """Find item name when the item is not in DB (tesseract fail)."""
    assert parser._find_item_name(["XBEREKS GRIP", "TWO-STONE RING"]) == ""


def test_parse_unidentified_title(parser: TitleParser):
    assert parser._parse_unidentified_title("SILK SLIPPERS\n\n") == "Silk Slippers"
    assert parser._parse_unidentified_title("SUN LEATHER\n\n") == "Sun Leather"


def test_parse_identified_title_error(parser: TitleParser):
    assert parser._parse_identified_title("BONES OF ULLR SILK SLIPPERS\n\n") == (
        "",
        "Silk Slippers",
    )


def test_apply_manual_corrections(parser: TitleParser):
    assert parser._apply_manual_corrections("Ruy Ring", parser.BASE_CORRECTIONS) == "Ruby Ring"
    assert (
        parser._apply_manual_corrections("Twoo-Point Arrow Quiver", parser.BASE_CORRECTIONS)
        == "Two-Point Arrow Quiver"
    )
