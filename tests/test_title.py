import pytest

from unique_matcher.items import ItemLoader
from unique_matcher.title import TitleParser


@pytest.fixture(scope="session")
def parser():
    item_loader = ItemLoader()
    item_loader.load()

    return TitleParser(item_loader)


def test_clean_title(parser: TitleParser):
    assert parser._clean_title("BLOODBOUND\nBONE ARMOUR\n\n") == "BLOODBOUND\nBONE ARMOUR\n\n"
    assert parser._clean_title("IMPERIAL STAFF\n\n") == "IMPERIAL STAFF\n\n"
    assert (
        parser._clean_title("BEREK’S GRIP\nTWO-STONE RING\n\n") == "BEREKS GRIP\nTWO-STONE RING\n\n"
    )
    assert (
        parser._clean_title("BONES OF ULLR\nSILK SLIPPERS\n\n")
        == "BONES OF ULLR\nSILK SLIPPERS\n\n"
    )
    assert parser._clean_title("SILK SLIPPERS\n\n") == "SILK SLIPPERS\n\n"


def test_parse_unidentified_title(parser: TitleParser):
    assert parser._parse_unidentified_title("SILK SLIPPERS\n\n") == "Silk Slippers"
    assert parser._parse_unidentified_title("SUN LEATHER\n\n") == "Sun Leather"


def test_parse_identified_title(parser: TitleParser):
    assert parser._parse_identified_title("BONES OF ULLR\nSILK SLIPPERS\n\n") == (
        "Bones_of_Ullr",
        "Silk Slippers",
    )


def test_apply_manual_corrections(parser: TitleParser):
    assert parser._apply_manual_corrections("Ruy Ring", parser.BASE_CORRECTIONS) == "Ruby Ring"
    assert (
        parser._apply_manual_corrections("Twoo-Point Arrow Quiver", parser.BASE_CORRECTIONS)
        == "Two-Point Arrow Quiver"
    )
