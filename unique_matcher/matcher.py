from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from loguru import logger
from PIL import Image

from unique_matcher.constants import (
    ITEM_MAX_SIZE,
    OPT_ALLOW_NON_FULLHD,
    OPT_CROP_SCREEN,
    OPT_CROP_SHADE,
    OPT_EARLY_FOUND,
    TEMPLATES_DIR,
)
from unique_matcher.exceptions import (
    CannotFindItemBase,
    CannotFindUniqueItem,
    CannotIdentifyUniqueItem,
    NotInFullHD,
)
from unique_matcher.generator import ItemGenerator
from unique_matcher.items import Item, ItemLoader

THRESHOLD = 0.3
THRESHOLD_CONTROL = 0.20
THRESHOLD_CONTROL_STRICT = 0.1


@dataclass
class ItemTemplate:
    """Helper class for the image template."""

    image: Image
    sockets: int
    fraction: int = 100
    size: tuple[int, int] = (0, 0)


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

        self.unique_one_line = Image.open(str(TEMPLATES_DIR / "unique-one-line-fullhd.png"))
        self.unique_two_line = Image.open(str(TEMPLATES_DIR / "unique-two-line-fullhd.png"))
        self.unique_one_line_end = Image.open(str(TEMPLATES_DIR / "unique-one-line-end-fullhd.png"))
        self.unique_two_line_end = Image.open(str(TEMPLATES_DIR / "unique-two-line-end-fullhd.png"))

    def get_best_result(self, results: list[MatchResult]) -> MatchResult:
        """Find the best result (min(min_val))."""
        return min(results, key=lambda res: res.min_val)

    def get_item_variants(self, item: Item) -> list[Image]:
        """Get a list of images for all socket variants of an item."""
        variants = []

        if item.sockets == 0:
            icon = Image.open(item.icon)
            icon.thumbnail(ITEM_MAX_SIZE, Image.Resampling.BILINEAR)

            return [ItemTemplate(image=icon, sockets=0)]

        for sockets in range(item.sockets, 0, -1):
            # Generate item with sockets in memory
            icon = Image.open(item.icon)
            template = ItemTemplate(
                image=self.generator.generate_image(icon, item, sockets),
                sockets=sockets,
            )
            variants.append(template)

        return variants

    def check_one(self, screen: np.ndarray, item: Item) -> MatchResult:
        """Check one screenshot against one item."""
        results = []

        possible_items = self.item_loader.filter(item.base)

        if len(possible_items) == 1:
            logger.success("Only one possible unique for base {}", item.base)
            return MatchResult(item, (0, 0), 0)

        item_variants = self.get_item_variants(item)

        logger.info("Item {} has {} variants", item.name, len(item_variants))

        for template in item_variants:
            template_cv = np.array(template.image)
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

    def _find_without_resizing(self, image: Image, screen: np.ndarray) -> tuple[int, int] | None:
        result = cv2.matchTemplate(
            screen,
            self._image_to_cv(image),
            cv2.TM_SQDIFF_NORMED,
        )
        min_val, _, min_loc, _ = cv2.minMaxLoc(result)

        return min_val, min_loc

    def _find_unique_control_start(self, screen: np.ndarray) -> tuple[tuple[int, int], bool] | None:
        """Find the start control point of a unique item.

        Return (x, y), is_identified.

        Return None if neither identified nor unidentified control point
        can be found.
        """
        min_val1, min_loc = self._find_without_resizing(self.unique_one_line, screen)

        logger.debug("Finding unique control start 1: min_val={}", min_val1)

        if min_val1 <= THRESHOLD_CONTROL:
            logger.info("Found unidentified item")
            return min_loc, False

        min_val2, min_loc = self._find_without_resizing(self.unique_two_line, screen)

        logger.debug("Finding unique control start 2: min_val={}", min_val2)

        if min_val2 <= THRESHOLD_CONTROL:
            logger.info("Found identified item")
            return min_loc, True

        logger.error(
            "Couldn't find unique control start, threshold is {}, line1_min={}, line2_min={}",
            THRESHOLD_CONTROL,
            min_val1,
            min_val2,
        )

        return None

    def _find_unique_control_end(
        self, screen: np.ndarray, is_identified: bool
    ) -> tuple[int, int] | None:
        """Find the end control point of a unique item.

        Return None if neither identified nor unidentified control point
        can be found.
        """
        if is_identified:
            min_val2, min_loc = self._find_without_resizing(self.unique_two_line_end, screen)

            logger.debug("Finding unique control end 2: min_val={}", min_val2)

            if min_val2 <= THRESHOLD_CONTROL:
                return min_loc
        else:
            min_val1, min_loc = self._find_without_resizing(self.unique_one_line_end, screen)

            logger.debug("Finding unique control end 1: min_val={}", min_val1)

            if min_val1 <= THRESHOLD_CONTROL:
                return min_loc

        logger.error(
            "Couldn't find unique control end, threshold is {}, line1_min={}, line2_min={}",
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

        if first is not None:
            if first > 10:
                logger.warning("Correcting vertical_crop.first, was {}", first)
                first = 0

            if first < 7:
                logger.warning("Correcting vertical_crop.first, was {}", first)
                first = 0

        if last is not None and last < 50:
            logger.warning("Correcting vertical_crop.last, was {}", last)
            last = len(arr)

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

        if first is not None:
            if first > 10:
                logger.warning("Correcting horizontal_crop.first, was {}", first)
                first = 0

            if first < 7:
                logger.warning("Correcting horizontal_crop.first, was {}", first)
                first = 0

        if last is not None and last < 50:
            logger.warning("Correcting horizontal_crop.last, was {}", last)
            last = len(arr)

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

        if first is not None and last is not None:
            subimg = subimg.crop((0, 0, subimg.width, last + 4))
        else:
            logger.warning("Horizontal crop failed, will attempt vertical")

        first, last = self._crop_vertical(arr, threshold)

        logger.debug("Vertical crop limits: first={}, last={}", first, last)

        if first is not None and last is not None:
            subimg = subimg.crop((subimg.width - last - 4, 0, subimg.width - first, subimg.height))

        return subimg

    def _clean_base_name(self, base: str) -> str:
        """Clean the raw base name as received from tesseract."""
        # Remove non-letter characters
        base = "".join([c for c in base if c.isalpha() or c in [" ", "\n", "-"]])

        # Remove bases with less than 3 characters
        base = " ".join([w for w in base.split() if len(w) > 2])

        if base == "CARNALMITTS":
            base = "CARNAL MITTS"

        return base

    def get_base_name(self, title_img: Image, is_identified: bool) -> str:
        """Get the item base name from the cropped out title image."""
        base_name_raw = pytesseract.image_to_string(title_img, "eng")
        base_name_raw = self._clean_base_name(base_name_raw)

        if is_identified:
            # Get only the second line if identified
            base_name_spl = base_name_raw.rstrip("\n").split("\n")

            if len(base_name_spl) > 1:
                base_name = base_name_spl[1].title()
            else:
                logger.warning("Failed to properly parse identified item name and base")

                # In case tesseract cannot read the name
                possibilities = [
                    " ".join(base_name_spl[0].split(" ")[-1:]),
                    " ".join(base_name_spl[0].split(" ")[-2:]),
                    " ".join(base_name_spl[0].split(" ")[-3:]),
                ]

                for possibility in possibilities:
                    if possibility.title() in self.item_loader.bases():
                        base_name = possibility.title()
                        break
                else:
                    base_name = "undefined"
        else:
            base_name = base_name_raw.replace("\n", "").title()

        # Remove prefixes
        base_name = base_name.replace("Superior ", "")

        # Check that the parsed base exists in item loader
        if base_name not in self.item_loader.bases():
            logger.error("Cannot detect item base, got: '{}'", base_name)
            raise CannotFindItemBase(f"Base '{base_name}' doesn't exist")

        logger.info("Item base: {}", base_name)

        return base_name

    def find_unique(self, screenshot: str | Path) -> tuple[Image, str]:
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

        min_loc_start, is_identified = self._find_unique_control_start(screen)

        if min_loc_start is None:
            raise CannotFindUniqueItem

        min_loc_end = self._find_unique_control_end(screen, is_identified)

        if min_loc_end is None:
            # TODO: Different exception
            raise CannotFindUniqueItem

        # Crop out the item image
        # (left, top, right, bottom)
        # Left is: position of guide - item width - space
        # Top is: position of guide + space
        # Right is: position of guide - space
        # Bottom is: position of guide + item height + space
        # Space is to allow some padding
        item_img = source_screen.crop(
            (
                min_loc_start[0] - ITEM_MAX_SIZE[0],
                min_loc_start[1],
                min_loc_start[0],
                min_loc_start[1] + ITEM_MAX_SIZE[1],
            )
        )
        size_orig = item_img.size

        logger.debug(
            "Unique item area has size: {}x{}px",
            item_img.width,
            item_img.height,
        )

        if OPT_CROP_SHADE:
            logger.debug("OPT_CROP_SHADE is enabled")
            item_img = self.crop_out_unique(item_img)

            logger.debug(
                "Unique item area cropped to size: {}x{}px",
                item_img.width,
                item_img.height,
            )

        if OPT_CROP_SHADE and item_img.size == size_orig:
            logger.error("Cropped out unique is the same size as original even with OPT_CROP_SHADE")

        # Crop out item name + base
        if is_identified:
            control_width, control_height = self.unique_two_line.size
        else:
            control_width, control_height = self.unique_one_line.size

        # The extra pixels are for tesseract, without them, it fails to read
        # anything at all
        title_img = source_screen.crop(
            (
                min_loc_start[0] + control_width - 24,
                min_loc_start[1] - 4,
                min_loc_end[0] + 24,
                min_loc_end[1] + control_height + 10,
            )
        )

        return item_img, self.get_base_name(title_img, is_identified)

    def find_item(self, screenshot: str) -> MatchResult:
        """Find an item in a screenshot."""
        logger.info("Finding item in screenshot: {}", screenshot)

        image, base = self.find_unique(screenshot)
        screen_crop = self._image_to_cv(image)

        results_all = []

        filtered_bases = self.item_loader.filter(base)
        logger.info("Searching through {} item base variants", len(filtered_bases))

        for item in filtered_bases:
            result = self.check_one(screen_crop, item)

            results_all.append(result)

        best_result = self.get_best_result(results_all)

        if best_result.min_val > 0.99:
            logger.error("Couldn't identify a unique item, even the best result had min_val == 1.0")
            raise CannotIdentifyUniqueItem

        return best_result
