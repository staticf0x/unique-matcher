from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from unique_matcher.constants import (
    ITEM_MAX_SIZE,
    OPT_CROP_SCREEN,
    OPT_EARLY_FOUND,
    ROOT_DIR,
)
from unique_matcher.generator import ItemGenerator
from unique_matcher.items import Item, ItemLoader

THRESHOLD = 0.01
THRESHOLD_CONTROL = 0.25


@dataclass
class ItemTemplate:
    """Helper class for the image template."""

    image: Image
    sockets: int


@dataclass
class MatchResult:
    """A class for the item/screenshot match result."""

    item: Item
    loc: tuple[int, int]
    min_val: float
    template: ItemTemplate | None = None

    def found(self) -> bool:
        return self.min_val <= THRESHOLD

    @property
    def confidence(self) -> float:
        """Turn min_val into percentage confidence."""
        if self.found():
            return 100.0

        return -100 / (1 - THRESHOLD) * (self.min_val - THRESHOLD) + 100


class Matcher:
    """Main class for matching items in a screenshot."""

    def __init__(self) -> None:
        self.generator = ItemGenerator()
        self.item_loader = ItemLoader()
        self.item_loader.load()

        self.unique_one_line = cv2.imread(str(ROOT_DIR / "templates" / "unique-one-line.png"))
        self.unique_one_line = cv2.cvtColor(self.unique_one_line, cv2.COLOR_RGB2GRAY)
        self.unique_two_line = cv2.imread(str(ROOT_DIR / "templates" / "unique-two-line.png"))
        self.unique_two_line = cv2.cvtColor(self.unique_two_line, cv2.COLOR_RGB2GRAY)

    def get_best_result(self, results: list[MatchResult]) -> MatchResult:
        """Find the best result (min(min_val))."""
        return min(results, key=lambda res: res.min_val)

    def get_item_variants(self, item: Item) -> list[Image]:
        """Get a list of images for all socket variants of an item."""
        variants = []

        if item.sockets == 0:
            icon = Image.open(item.icon)
            icon.thumbnail(ITEM_MAX_SIZE, Image.Resampling.BICUBIC)

            return [ItemTemplate(image=icon, sockets=0)]

        for sockets in range(item.sockets, 0, -1):
            # Generate item with sockets in memory
            template = ItemTemplate(
                image=self.generator.generate_image(item.icon, sockets, item.cols),
                sockets=sockets,
            )
            variants.append(template)

        return variants

    def check_one(self, screen: np.ndarray, item: Item) -> MatchResult:
        """Check one screenshot against one item."""
        results = []

        item_variants = self.get_item_variants(item)

        for template in item_variants:
            for fraction in range(100, 0, -5):
                resized = template.image.copy()
                resized.thumbnail(
                    (
                        int(ITEM_MAX_SIZE[0] * fraction / 100),
                        int(ITEM_MAX_SIZE[1] * fraction / 100),
                    ),
                    Image.Resampling.BICUBIC,
                )

                template_cv = np.array(resized)
                template_cv = cv2.cvtColor(template_cv, cv2.COLOR_RGBA2GRAY)

                # Match against the screenshot
                result = cv2.matchTemplate(screen, template_cv, cv2.TM_SQDIFF_NORMED)
                min_val, _, min_loc, _ = cv2.minMaxLoc(result)

                match_result = MatchResult(item, min_loc, min_val, template)

                if OPT_EARLY_FOUND and match_result.found():
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

    def load_screen(self, screenshot: str | Path) -> np.ndarray:
        """Load a screenshot from file into OpenCV format."""
        screen = cv2.imread(str(screenshot))
        screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

        if OPT_CROP_SCREEN:
            screen = screen[1080 // 4 :, 1920 // 2 :]

        return screen

    def load_screen_as_image(self, screenshot: str | Path) -> Image:
        return Image.open(str(screenshot))

    def _find_unique_control(self, screen: np.ndarray) -> tuple[int, int] | None:
        """Find the control point of a unique item.

        Return None if neither identified nor unidentified control point
        can be found.
        """
        result = cv2.matchTemplate(screen, self.unique_one_line, cv2.TM_SQDIFF_NORMED)
        min_val, _, min_loc, _ = cv2.minMaxLoc(result)

        if min_val <= THRESHOLD_CONTROL:
            return min_loc

        result = cv2.matchTemplate(screen, self.unique_two_line, cv2.TM_SQDIFF_NORMED)
        min_val, _, min_loc, _ = cv2.minMaxLoc(result)

        if min_val <= THRESHOLD_CONTROL:
            return min_loc

        return None

    def _image_to_cv(self, image: Image) -> np.ndarray:
        image_cv = np.array(image)
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2GRAY)

        return image_cv

    def find_unique(self, screenshot: str | Path) -> Image:
        """Return a cropped part of the screenshot with the unique.

        If it cannot be found, returns the original screenshot.
        """
        source_screen = Image.open(str(screenshot))  # Original screenshot
        screen = self.load_screen_as_image(screenshot)  # CV2 screenshot

        min_loc = self._find_unique_control(self._image_to_cv(screen))

        if min_loc is None:
            # Return original screenshot in CV2 format
            return screen

        # Crop out the item image
        source_screen = source_screen.crop(
            (min_loc[0] - 100, min_loc[1], min_loc[0], min_loc[1] + 200)
        )
        source_screen.show()

        return source_screen

    def find_item(self, screenshot: str) -> MatchResult | None:
        """Find an item in a screenshot.

        Returns None if no item was found in the screenshot.
        """
        screen_crop = self._image_to_cv(self.find_unique(screenshot))

        results_all = []

        for item in self.item_loader:
            result = self.check_one(screen_crop, item)

            results_all.append(result)

        return self.get_best_result(results_all)
