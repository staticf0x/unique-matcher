import os
from dataclasses import dataclass

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from unique_matcher.constants import DEBUG, ROOT_DIR
from unique_matcher.generator import ItemGenerator

THRESHOLD = 0.33
ITEM_DIR = ROOT_DIR / "items"


@dataclass
class Item:
    """Represent a single item."""

    name: str
    icon: str
    sockets: int = 6


@dataclass
class MatchResult:
    """A class for the item/screenshot match result."""

    item: Item
    loc: tuple[int, int]
    min_val: float

    def found(self) -> bool:
        return self.min_val <= THRESHOLD

    @property
    def confidence(self) -> float:
        """Turn min_val into percentage confidence."""
        if self.found():
            return 100.0

        return -100 / (1 - THRESHOLD) * (self.min_val - THRESHOLD) + 100


@dataclass
class ItemTemplate:
    """Helper class for the image template."""

    image: Image
    sockets: int


class Matcher:
    """Main class for matching items in a screenshot."""

    def __init__(self) -> None:
        self.generator = ItemGenerator()
        self.items = self.load_items()

    def load_items(self) -> list[Item]:
        """Load all items."""
        items = []

        for file in sorted(os.listdir(ITEM_DIR)):
            item = Item(
                name=file.replace(".png", ""),
                icon=os.path.join(ITEM_DIR, file),
            )
            items.append(item)

        return items

    def get_best_result(self, results: list[MatchResult]) -> MatchResult:
        """Find the best result (min(min_val))."""
        return min(results, key=lambda res: res.min_val)

    def get_item_variants(self, item: Item) -> list[Image]:
        """Get a list of images for all socket variants of an item."""
        variants = []

        if item.sockets == 0:
            return [ItemTemplate(image=Image.open(item.icon), sockets=0)]

        for sockets in range(item.sockets, 0, -1):
            # Generate item with sockets in memory
            template = ItemTemplate(
                image=self.generator.generate_image(item.icon, sockets),
                sockets=sockets,
            )
            variants.append(template)

            if DEBUG:
                template.image.save(f"debug/{item.name}_{template.sockets}s.png")

        return variants

    def check_one(self, screen: np.ndarray, item: Item) -> MatchResult:
        """Check one screenshot against one item."""
        results = []
        item_variants = self.get_item_variants(item)

        for template in item_variants:
            template_cv = np.array(template.image)
            template_cv = cv2.cvtColor(template_cv, cv2.COLOR_RGBA2GRAY)

            # Match against the screenshot
            result = cv2.matchTemplate(screen, template_cv, cv2.TM_SQDIFF_NORMED)
            min_val, _, min_loc, _ = cv2.minMaxLoc(result)

            match_result = MatchResult(item, min_loc, min_val)

            if match_result.found():
                # Optimization, sort of... We're only interested in finding
                # the item itself, not how many sockets it has, so it's
                # fine to return early
                logger.success(
                    "Found item {} early, sockets={}, min_val={}",
                    match_result.item.name,
                    template.sockets,
                    match_result.min_val,
                )
                return match_result

            results.append(match_result)

        # If we couldn't find the item immediately, return the best result
        # This is useful mainly for benchmarking and tests
        return self.get_best_result(results)

    def load_screen(self, screenshot: str) -> np.ndarray:
        """Load a screenshot from file into OpenCV format."""
        screen = cv2.imread(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

        if DEBUG:
            screen = screen[:, 1920 // 2 :]

        return screen

    def find_item(self, screenshot: str) -> MatchResult | None:
        """Find an item in a screenshot.

        Returns None if no item was found in the screenshot.
        """
        screen = self.load_screen(screenshot)

        for item in self.items:
            result = self.check_one(screen, item)

            if result.found():
                logger.success(
                    "Found item {} in {}, min_val={}", result.item.name, screenshot, result.min_val
                )

                return result

        return None
