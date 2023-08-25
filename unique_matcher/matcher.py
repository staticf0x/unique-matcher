from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from unique_matcher.constants import (
    ITEM_MAX_SIZE,
    OPT_ALLOW_NON_FULLHD,
    OPT_CROP_SCREEN,
    OPT_CROP_SHADE,
    OPT_EARLY_FOUND,
    ROOT_DIR,
)
from unique_matcher.exceptions import CannotFindUniqueItem, NotInFullHD
from unique_matcher.generator import ItemGenerator
from unique_matcher.items import Item, ItemLoader

THRESHOLD = 0.2
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

        logger.info("Item {} has {} variants", item.name, len(item_variants))

        for template in item_variants:
            for fraction in range(100, 0, -5):
                resized = template.image.copy()
                resized.thumbnail(
                    (
                        int(min(ITEM_MAX_SIZE[0], len(screen)) * fraction / 100),
                        int(min(ITEM_MAX_SIZE[1], len(screen[0])) * fraction / 100),
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
            logger.debug("OPT_CROP_SCREEN is enabled")
            screen = screen[:, 1920 // 2 :]

        return screen

    def load_screen_as_image(self, screenshot: str | Path) -> Image:
        return Image.open(str(screenshot))

    def _find_unique_control(self, screen: np.ndarray) -> tuple[int, int] | None:
        """Find the control point of a unique item.

        Return None if neither identified nor unidentified control point
        can be found.
        """
        result = cv2.matchTemplate(screen, self.unique_one_line, cv2.TM_SQDIFF_NORMED)
        min_val1, _, min_loc, _ = cv2.minMaxLoc(result)

        logger.debug("Finding unique control 1: min_val={}", min_val1)

        if min_val1 <= THRESHOLD_CONTROL:
            return min_loc

        result = cv2.matchTemplate(screen, self.unique_two_line, cv2.TM_SQDIFF_NORMED)
        min_val2, _, min_loc, _ = cv2.minMaxLoc(result)

        logger.debug("Finding unique control 2: min_val={}", min_val2)

        if min_val2 <= THRESHOLD_CONTROL:
            return min_loc

        logger.error(
            "Couldn't find unique control, threshold is {}, line1_min={}, line2_min={}",
            THRESHOLD_CONTROL,
            min_val1,
            min_val2,
        )

        return None

    def _image_to_cv(self, image: Image) -> np.ndarray:
        image_cv = np.array(image)
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2GRAY)

        return image_cv

    def _get_crop_threshold(self, arr: np.ndarray) -> int:
        """Return the threshold (pixel value) where the shade should be cut off."""
        # Number of pixels in image for normalization
        pixels = len(arr) * len(arr[0])

        # Convert to grayscale for simplification
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        # Calculate histogram into 5 bins (51 values per bin)
        hist = cv2.calcHist([arr], [0], None, [5], (0, 256), accumulate=True)

        # Normalize to [0, 1]
        hist_perc = hist / pixels

        if hist_perc[0] >= 0.8:
            # Very dark
            logger.debug("Item is on a very dark background")
            return 15

        if hist_perc[0] >= 0.6:
            # Dark
            logger.debug("Item is on a mildly dark background")
            return 20

        if hist_perc[1] >= 0.5:
            # Bright
            logger.debug("Item is on a bright background")
            return 50

        return 50

    def _is_shade(self, row: np.ndarray, threshold: int) -> bool:
        """Return True if a row is a shade."""
        count_r = len([px for px in row[:, 0] if px < threshold])
        count_g = len([px for px in row[:, 1] if px < threshold])
        count_b = len([px for px in row[:, 2] if px < threshold])

        # At least 30px, the smallest items (rings, etc...) are at least 50px
        return min(count_r, count_g, count_b) > 25

    def _crop_vertical(self, arr: np.ndarray, threshold: int) -> tuple[int, int]:
        """Return (first, last) positions of lines that contain the shade."""
        first = last = None
        arr = np.rot90(arr, 1)

        logger.debug("Running vertical crop")

        for row in range(len(arr)):
            is_it = self._is_shade(arr[row, :], threshold)

            if is_it and first is None:
                first = row

            if first and is_it:
                last = row

        return first, last

    def _crop_horizontal(self, arr: np.ndarray, threshold: int) -> tuple[int, int]:
        """Return (first, last) positions of lines that contain the shade."""
        first = last = None

        logger.debug("Running horizontal crop")

        for row in range(len(arr)):
            is_it = self._is_shade(arr[row, :], threshold)

            if is_it and first is None:
                first = row

            if first and is_it:
                last = row

        return first, last

    def crop_out_unique(self, image: Image) -> Image:
        """Crop out the unique item.

        This will remove extra background, so that only
        the actual item artwork is returned.
        """
        arr = np.array(image)
        threshold = self._get_crop_threshold(arr)

        logger.debug("Crop value threshold: {}", threshold)

        subimg = image.copy()
        first, last = self._crop_horizontal(arr, threshold)

        logger.debug("Horizontal crop limits: first={}, last={}", first, last)

        if first and last:
            subimg = subimg.crop((0, 0, subimg.width, last + 2))
        else:
            logger.warning("Horizontal crop failed, will attempt vertical")

        first, last = self._crop_vertical(arr, threshold)

        logger.debug("Vertical crop limits: first={}, last={}", first, last)

        if first and last:
            subimg = subimg.crop((subimg.width - last - 2, 0, subimg.width - first, subimg.height))

        return subimg

    def find_unique(self, screenshot: str | Path) -> Image:
        """Return a cropped part of the screenshot with the unique.

        If it cannot be found, returns the original screenshot.
        """
        source_screen = Image.open(str(screenshot))  # Original screenshot
        screen = self.load_screen(screenshot)  # CV2 screenshot

        if source_screen.size != (1920, 1080):
            logger.warning(
                "Screenshot size is not 1920x1080px, accuracy will be impacted"
                " (real size is {}x{}px)",
                source_screen.width,
                source_screen.height,
            )

            if not OPT_ALLOW_NON_FULLHD:
                logger.error(
                    "OPT_ALLOW_NON_FULLHD is disabled and screenshot isn't 1920x1080px, aborting"
                )
                raise NotInFullHD

        min_loc = self._find_unique_control(screen)

        if min_loc is None:
            raise CannotFindUniqueItem

        # Crop out the item image
        source_screen = source_screen.crop(
            (min_loc[0] - 100, min_loc[1], min_loc[0], min_loc[1] + 200)
        )
        size_orig = source_screen.size

        if OPT_CROP_SHADE:
            logger.debug("OPT_CROP_SHADE is enabled")
            source_screen = self.crop_out_unique(source_screen)

        logger.debug(
            "Unique item area size: {}x{}px",
            source_screen.width,
            source_screen.height,
        )

        if OPT_CROP_SHADE and source_screen.size == size_orig:
            logger.error("Cropped out unique is the same size as original even with OPT_CROP_SHADE")

        return source_screen

    def find_item(self, screenshot: str) -> MatchResult | None:
        """Find an item in a screenshot.

        Returns None if no item was found in the screenshot.
        """
        logger.info("Finding item in screenshot: {}", screenshot)
        screen_crop = self._image_to_cv(self.find_unique(screenshot))

        results_all = []

        for item in self.item_loader:
            result = self.check_one(screen_crop, item)

            results_all.append(result)

        return self.get_best_result(results_all)
