"""Module for matching unique items."""
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from unique_matcher import utils
from unique_matcher.bases import BaseDetector
from unique_matcher.constants import ITEM_MAX_SIZE, OPT_ALLOW_NON_FULLHD, TEMPLATES_DIR
from unique_matcher.exceptions import (
    CannotFindUniqueItem,
    CannotIdentifyUniqueItem,
    InvalidTemplateDimensions,
    NotInFullHD,
)
from unique_matcher.generator import ItemGenerator
from unique_matcher.items import Item, ItemLoader

# Threshold at which we must discard the result because it's inconclusive
# even amongst the already filtered bases.
THRESHOLD_DISCARD = 0.99

# Threshold for the control guides (item title decorations).
# Has to be low enough to not allow other clutter to get in.
# Typically the min_val of guides is ~0.06.
THRESHOLD_CONTROL = 0.16


@dataclass
class ItemTemplate:
    """Helper class for the image template."""

    image: Image.Image
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


class Matcher:
    """Main class for matching items in a screenshot."""

    def __init__(self) -> None:
        self.generator = ItemGenerator()
        self.item_loader = ItemLoader()
        self.item_loader.load()
        self.base_detector = BaseDetector(self.item_loader)

        self.unique_one_line = Image.open(str(TEMPLATES_DIR / "unique-one-line-fullhd.png"))
        self.unique_two_line = Image.open(str(TEMPLATES_DIR / "unique-two-line-fullhd.png"))
        self.unique_one_line_end = Image.open(str(TEMPLATES_DIR / "unique-one-line-end-fullhd.png"))
        self.unique_two_line_end = Image.open(str(TEMPLATES_DIR / "unique-two-line-end-fullhd.png"))

    def get_best_result(self, results: list[MatchResult]) -> MatchResult:
        """Find the best result (min(min_val))."""
        return min(results, key=lambda res: res.min_val)

    def get_item_variants(self, item: Item) -> list[ItemTemplate]:
        """Get a list of images for all socket variants of an item."""
        variants = []

        if item.sockets == 0:
            icon = Image.open(item.icon)
            icon.thumbnail(ITEM_MAX_SIZE, Image.Resampling.BILINEAR)

            if item.width != 2 or item.height != 4:
                logger.debug("Changing item base image dimensions")
                icon.thumbnail(
                    (
                        int(ITEM_MAX_SIZE[0] * (item.width / 2)),
                        int(ITEM_MAX_SIZE[1] * (item.height / 4)),
                    ),
                    Image.Resampling.BILINEAR,
                )

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

    def check_one(self, image: Image.Image, item: Item) -> MatchResult:
        """Check one screenshot against one item."""
        results = []

        possible_items = self.item_loader.filter(item.base)

        if len(possible_items) == 1:
            logger.success("Only one possible unique for base {}", item.base)
            return MatchResult(item, (0, 0), 0)

        item_variants = self.get_item_variants(item)

        logger.info("Item {} has {} variant(s)", item.name, len(item_variants))

        image = self.crop_out_unique_by_dimensions(image, item)
        screen = utils.image_to_cv(image)

        for template in item_variants:
            if template.image.width > image.width or template.image.height > image.height:
                logger.error(
                    "Template image is larger than unique item: {}x{}px vs {}x{}px",
                    template.image.width,
                    template.image.height,
                    image.width,
                    image.height,
                )
                raise InvalidTemplateDimensions(
                    "Template image is larger than unique item: {}x{}px vs {}x{}px".format(
                        template.image.width,
                        template.image.height,
                        image.width,
                        image.height,
                    )
                )

            template_cv = np.array(template.image)
            template_cv = cv2.cvtColor(template_cv, cv2.COLOR_RGBA2GRAY)

            # Match against the screenshot
            result = cv2.matchTemplate(screen, template_cv, cv2.TM_SQDIFF_NORMED)
            min_val, _, min_loc, _ = cv2.minMaxLoc(result)

            match_result = MatchResult(item, min_loc, min_val, template)
            results.append(match_result)

        # If we couldn't find the item immediately, return the best result
        # This is useful mainly for benchmarking and tests
        return self.get_best_result(results)

    def load_screen(self, screenshot: str | Path) -> np.ndarray:
        """Load a screenshot from file into OpenCV format."""
        screen = cv2.imread(str(screenshot))
        return cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

    def _find_without_resizing(
        self, image: Image.Image, screen: np.ndarray
    ) -> tuple[float, tuple[int, int]]:
        result = cv2.matchTemplate(
            screen,
            utils.image_to_cv(image),
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

    def crop_out_unique_by_dimensions(self, image: Image.Image, item: Item) -> Image.Image:
        """Crop out the unique item image based on its inventory w/h."""
        if item.is_smaller_than_full():
            logger.debug("Cropping image based on item width and height")
            image = image.crop(
                (
                    int(image.width * (1 - item.width / 2)),
                    0,
                    image.width,
                    int(image.height * item.height / 4),
                )
            )

        return image

    def find_unique(self, screenshot: str | Path) -> tuple[Image.Image, str]:
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

        res = self._find_unique_control_start(screen)

        if res is None:
            raise CannotFindUniqueItem

        min_loc_start, is_identified = res
        min_loc_end = self._find_unique_control_end(screen, is_identified)

        if min_loc_end is None:
            # TODO: Different exception
            raise CannotFindUniqueItem

        # Crop out the item image: (left, top, right, bottom)
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

        logger.debug(
            "Unique item area has size: {}x{}px",
            item_img.width,
            item_img.height,
        )

        # Crop out item name + base
        if is_identified:
            control_width, control_height = self.unique_two_line.size
        else:
            control_width, control_height = self.unique_one_line.size

        # The extra pixels are for tesseract, without them, it fails to read
        # anything at all
        title_img = source_screen.crop(
            (
                min_loc_start[0] + control_width - 6,
                min_loc_start[1] + 4,
                min_loc_end[0] + 6,
                min_loc_end[1] + control_height - 6,
            )
        )

        return item_img, self.base_detector.get_base_name(title_img, is_identified)

    def find_item(self, screenshot: str) -> MatchResult:
        """Find an item in a screenshot."""
        logger.info("Finding item in screenshot: {}", screenshot)

        image, base = self.find_unique(screenshot)

        results_all = []

        filtered_bases = self.item_loader.filter(base)
        logger.info("Searching through {} item base variants", len(filtered_bases))

        for item in filtered_bases:
            result = self.check_one(image, item)

            results_all.append(result)

        best_result = self.get_best_result(results_all)

        if best_result.min_val > THRESHOLD_DISCARD:
            logger.error(
                "Couldn't identify a unique item, even the best result "
                "was above THRESHOLD_DISCARD (min_val={})",
                result.min_val,
            )
            raise CannotIdentifyUniqueItem

        if aliases := self.item_loader.item_aliases(best_result.item):
            logger.warning(
                "Found aliased item: {}, aliases:\n{}",
                best_result.item.name,
                "\n".join([item.name for item in aliases]),
            )

        return best_result
