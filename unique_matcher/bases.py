from typing import ClassVar

import pytesseract
from loguru import logger
from PIL import Image, ImageOps

from unique_matcher.exceptions import CannotFindItemBase
from unique_matcher.items import ItemLoader


class BaseDetector:
    """Class for detecting the item base."""

    # Known issues that are easy to correct
    CORRECTIONS: ClassVar[dict[str, str]] = {
        "Rusy Ring": "Ruby Ring",
        "Tronscale Gauntlets": "Ironscale Gauntlets",
        "Twoo-Point Arrow Quiver": "Two-Point Arrow Quiver",
        "Twwo-Stone Ring": "Two-Stone Ring",
        "Unsset Ring": "Unset Ring",
        "Ruy Ring": "Ruby Ring",
        "Goathide Booots": "Goathide Boots",
    }

    def __init__(self, item_loader: ItemLoader) -> None:
        self.item_loader = item_loader

    def _clean_base_name(self, base: str) -> str:
        """Clean the raw base name as received from tesseract."""
        # Remove non-letter characters
        base = "".join([c for c in base if c.isalpha() or c in [" ", "\n", "-"]])

        # Remove bases with fewer than 3 characters
        lines = base.split("\n")
        lines = [" ".join([w for w in line.split() if len(w) > 2]) for line in lines]

        return "\n".join(lines)

    def _get_unidentified_base_name(self, base_name_raw: str) -> str:
        """Get a base of an unidentified item."""
        return base_name_raw.replace("\n", "").title()

    def _get_identified_base_name(self, base_name_raw: str) -> str:
        """Get a base of an identified item."""
        # Get only the second line if identified
        base_name_spl = base_name_raw.rstrip("\n").split("\n")

        if len(base_name_spl) > 1:
            # Two lines (item name + base)
            return base_name_spl[1].title()

        # At this point, tesseract likely incorrectly determined
        # new lines, so we have to do some more magic
        logger.warning("Failed to properly parse identified item name and base")

        # In case tesseract cannot read the name,
        # prepare possibilities from 3 words, 2 words and 1 word
        possibilities = [
            " ".join(base_name_spl[0].split(" ")[-3:]),
            " ".join(base_name_spl[0].split(" ")[-2:]),
            " ".join(base_name_spl[0].split(" ")[-1:]),
        ]

        for possibility in possibilities:
            if possibility.title() in self.item_loader.bases():
                return possibility.title()

        return "undefined"

    def _apply_manual_corrections(self, base_name: str) -> str:
        """Apply manual corrections specified in self.CORRECTIONS."""
        for original, corrected in self.CORRECTIONS.items():
            if original in base_name:
                base_name = base_name.replace(original, corrected)

        return base_name

    def get_base_name(self, title_img: Image.Image, is_identified: bool) -> str:
        """Get the item base name from the cropped out title image."""
        # Add 1px white border to help tesseract
        title_img = ImageOps.expand(title_img, border=1, fill="white")

        base_name_raw = pytesseract.image_to_string(title_img, "eng")
        base_name_raw = self._clean_base_name(base_name_raw)

        if is_identified:
            base_name = self._get_identified_base_name(base_name_raw)
        else:
            base_name = self._get_unidentified_base_name(base_name_raw)

        # Remove prefixes
        base_name = base_name.replace("Superior ", "")

        # Additional corrections
        base_name = self._apply_manual_corrections(base_name)

        # Check that the parsed base exists in item loader
        if base_name not in self.item_loader.bases():
            logger.error("Cannot detect item base, got: '{}'", base_name)
            raise CannotFindItemBase(f"Base '{base_name}' doesn't exist")

        logger.info("Item base: {}", base_name)

        return base_name
