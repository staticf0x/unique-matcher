"""Parse item titles."""
import re
from typing import ClassVar

import pytesseract
from loguru import logger
from PIL import Image, ImageOps

from unique_matcher.constants import OPT_FIND_BY_NAME_RAISE
from unique_matcher.matcher.exceptions import CannotFindItemBase
from unique_matcher.matcher.items import ItemLoader
from unique_matcher.matcher.utils import normalize_item_name


class TitleParser:
    """Class for parsing item titles (base and name)."""

    # Known issues that are easy to correct
    BASE_CORRECTIONS: ClassVar[dict[str, str]] = {
        "Rusy Ring": "Ruby Ring",
        "Tronscale Gauntlets": "Ironscale Gauntlets",
        "Twoo-Point Arrow Quiver": "Two-Point Arrow Quiver",
        "Twwo-Stone Ring": "Two-Stone Ring",
        "Unsset Ring": "Unset Ring",
        "Ruy Ring": "Ruby Ring",
        "Goathide Booots": "Goathide Boots",
    }

    ITEM_CORRECTIONS: ClassVar[dict[str, str]] = {
        "Dyyaadus": "Dyadus",
        "Heup_of_All": "Le_Heup_of_All",
        "Hyrrls_Bite": "Hyrris_Bite",
        "Hyrrs_Bite": "Hyrris_Bite",
        "Kondoss_Pride": "Kondos_Pride",
        "Night_Hold": "Nights_Hold",
        "Nomiics_Storm": "Nomics_Storm",
        "Rigwaldss_Command": "Rigwalds_Command",
    }

    def __init__(self, item_loader: ItemLoader) -> None:
        self.item_loader = item_loader

    def _clean_title(self, title: str) -> str:
        """Clean the raw title as received from tesseract."""
        # Remove non-letter characters
        title = "".join([c for c in title if c.isalpha() or c in [" ", "\n", "-"]])

        try:
            # Remove incorrectly parse possesive
            if title.split(" ")[1] == "S":
                title = title.replace(" S", "S", 1)
        except IndexError:
            # This was a one word title
            pass

        # Remove bases with fewer than 3 characters
        okay_words = ["OF"]

        lines = title.split("\n")
        lines = [
            " ".join([w for w in line.split() if len(w) > 2 or w in okay_words]) for line in lines
        ]

        return "\n".join(lines)

    def _parse_unidentified_title(self, title_raw: str) -> str:
        """Get a base of an unidentified item."""
        return title_raw.replace("\n", "").title()

    def _find_item_name(self, title_parts: list[str]) -> str:
        """Find item name in title parts."""
        item_name = (
            normalize_item_name(title_parts[0].title())
            .replace("_Of_", "_of_")
            .replace("_The_", "_the_")
            .replace("_And_", "_and_")
            .replace("_From_", "_from_")
        )

        # Fix all "dash upper case" letters, like Three-Step -> Three-step
        for m in re.finditer(r"\-(\w)", item_name):
            item_name = (
                item_name[: m.start()]
                + item_name[m.start() : m.end()].lower()
                + item_name[m.end() :]
            )

        # Apply manual corrections
        item_name = self._apply_manual_corrections(item_name, self.ITEM_CORRECTIONS)

        try:
            item = self.item_loader.get(item_name)
        except KeyError:
            logger.error("Couldn't find item name: {}", item_name)

            if OPT_FIND_BY_NAME_RAISE:
                raise

            return ""

        logger.info("Item name (normalized): {}", item_name)
        return item.file

    def _parse_identified_title(self, title_raw: str) -> tuple[str, str]:
        """Get a base and name of an identified item."""
        # Get only the second line if identified
        title_spl = title_raw.rstrip("\n").split("\n")
        item_name = self._find_item_name(title_spl)

        if len(title_spl) > 1:
            # Two lines (item name + base)
            return item_name, title_spl[1].title()

        # At this point, tesseract likely incorrectly determined
        # new lines, so we have to do some more magic
        logger.warning("Failed to properly parse identified item name and base")

        # In case tesseract cannot read the name,
        # prepare possibilities from 3 words, 2 words and 1 word
        possibilities = [
            " ".join(title_spl[0].split(" ")[-3:]),
            " ".join(title_spl[0].split(" ")[-2:]),
            " ".join(title_spl[0].split(" ")[-1:]),
        ]

        for possibility in possibilities:
            if possibility.title() in self.item_loader.bases():
                return item_name, possibility.title()

        return item_name, "undefined"

    def _apply_manual_corrections(self, name: str, lookup: dict[str, str]) -> str:
        """Apply manual corrections specified in lookup."""
        for original, corrected in lookup.items():
            if original in name:
                name = name.replace(original, corrected)

        return name

    def parse_title(self, title_img: Image.Image, *, is_identified: bool) -> tuple[str, str]:
        """Get the item base and name from the cropped out title image."""
        # Add 1px white border to help tesseract
        title_img = ImageOps.expand(title_img, border=1, fill="white")

        title_raw = pytesseract.image_to_string(title_img, "eng")
        title_raw = self._clean_title(title_raw)

        if is_identified:
            item_name, base_name = self._parse_identified_title(title_raw)
        else:
            item_name = ""
            base_name = self._parse_unidentified_title(title_raw)

        # Remove prefixes
        base_name = base_name.replace("Superior ", "")

        # Additional corrections
        base_name = self._apply_manual_corrections(base_name, self.BASE_CORRECTIONS)

        # Check that the parsed base exists in item loader
        if base_name not in self.item_loader.bases():
            logger.error("Cannot detect item base, got: '{}'", base_name)
            msg = f"Base '{base_name}' doesn't exist"
            raise CannotFindItemBase(msg)

        logger.info("Item base: {}", base_name)

        return base_name, item_name
