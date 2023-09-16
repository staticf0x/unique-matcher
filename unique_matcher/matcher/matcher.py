"""Module for matching unique items."""
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from unique_matcher.constants import (
    DEBUG,
    ITEM_MAX_SIZE,
    OPT_ALLOW_NON_FULLHD,
    OPT_FIND_ITEM_BY_NAME,
    TEMPLATES_DIR,
)
from unique_matcher.matcher import utils
from unique_matcher.matcher.exceptions import (
    CannotFindUniqueItem,
    CannotIdentifyUniqueItem,
    InvalidTemplateDimensions,
    NotInFullHD,
)
from unique_matcher.matcher.generator import ItemGenerator
from unique_matcher.matcher.items import Item, ItemLoader
from unique_matcher.matcher.title import TitleParser

# Threshold at which we must discard the result because it's inconclusive
# even amongst the already filtered bases.
THRESHOLD_DISCARD = 0.96

# Threshold for the control guides (item title decorations).
# Has to be low enough to not allow other clutter to get in.
# Typically the min_val of guides is ~0.06.
THRESHOLD_CONTROL = 0.16

# Threshold for discarding results based on the distance
# in either min_val or hist_val between the best result
# and the second best result.
# If the distance is too low (lower than THRESHOLD_RESULT_DISTANCE),
# the result will be discarded for the detection not being accurate enough.
THRESHOLD_RESULT_DISTANCE = 0.02


@dataclass
class ItemTemplate:
    """Helper class for the image template."""

    image: Image.Image
    sockets: int


@dataclass
class CroppedItemInfo:
    """Helper class for the cropped out part with unique item info."""

    image: Image.Image
    base: str
    name: str
    identified: bool


class MatchedBy(Enum):
    """How the item was matched."""

    TEMPLATE_MATCH = 0
    HISTOGRAM_MATCH = 1
    ONLY_UNIQUE_FOR_BASE = 2
    ITEM_NAME = 3

    def __str__(self) -> str:
        match self:
            case self.TEMPLATE_MATCH:
                return "Template matching"
            case self.HISTOGRAM_MATCH:
                return "Histogram comparison"
            case self.ONLY_UNIQUE_FOR_BASE:
                return "Only unique for the base"
            case self.ITEM_NAME:
                return "Item name"
            case _:
                raise ValueError


@dataclass
class MatchResult:
    """A class for the item/screenshot match result."""

    item: Item
    loc: tuple[int, int]
    identified: bool | None
    matched_by: MatchedBy
    min_val: float
    hist_val: float = 0.0
    template: ItemTemplate | None = None


class MatchingAlgorithm(Enum):
    """Enum for matching algorithm during get_best_result."""

    DEFAULT = 0
    VARIANTS_ONLY = 1
    HISTOGRAM = 2


class Matcher:
    """Main class for matching items in a screenshot."""

    FORCE_HISTOGRAM_MATCHING: ClassVar[list[str]] = [
        "Two-Stone Ring",
    ]

    def __init__(self) -> None:
        self.generator = ItemGenerator()
        self.item_loader = ItemLoader()
        self.item_loader.load()
        self.title_parser = TitleParser(self.item_loader)

        self.unique_one_line = Image.open(str(TEMPLATES_DIR / "unique-one-line-fullhd.png"))
        self.unique_one_line_end = Image.open(str(TEMPLATES_DIR / "unique-one-line-end-fullhd.png"))

        self.unique_two_line = Image.open(str(TEMPLATES_DIR / "unique-two-line-fullhd.png"))
        self.unique_two_line_end = Image.open(str(TEMPLATES_DIR / "unique-two-line-end-fullhd.png"))

        self.unique_two_line_cmp = Image.open(
            str(TEMPLATES_DIR / "unique-two-line-fullhd-compressed.png")
        )
        self.unique_two_line_end_cmp = Image.open(
            str(TEMPLATES_DIR / "unique-two-line-end-fullhd-compressed.png")
        )

        self.debug_info: dict[str, Any] = {}

    def _get_distance_from_best(self, results: list[MatchResult]) -> tuple[float, float]:
        """Get the distance in min_val and hist_val between 1st and 2nd result.

        If there is <= 1 result, return (1.0, 1.0).
        """
        if len(results) <= 1:
            return 1.0, 1.0

        # Sort the results lowest to highest
        min_val = sorted(results, key=lambda res: res.min_val)
        hist_val = sorted(results, key=lambda res: res.min_val)

        # Calculate distances between 1st and 2nd result
        dist_min_val = abs(min_val[0].min_val - min_val[1].min_val)
        dist_hist_val = abs(hist_val[0].hist_val - hist_val[1].hist_val)

        # Warn if under threshold
        if dist_min_val < THRESHOLD_RESULT_DISTANCE:
            logger.warning("min_val distance too low: {}", dist_min_val)

        if dist_hist_val < THRESHOLD_RESULT_DISTANCE:
            logger.warning("hist_val distance too low: {}", dist_hist_val)

        # Compare which method is more accurate
        if dist_min_val < dist_hist_val:
            logger.debug("Histogram comparison seems to be more precise than template matching")
        else:
            logger.debug("Template matching seems to be more precise than histogram comparison")

        return dist_min_val, dist_hist_val

    def get_best_result(
        self,
        results: list[MatchResult],
        algorithm: MatchingAlgorithm = MatchingAlgorithm.DEFAULT,
    ) -> MatchResult:
        """Find the best result (min(min_val) or min(hist_val))."""
        logger.debug("Matching algorithm: {}", algorithm)

        dist_min_val, dist_hist_val = self._get_distance_from_best(results)

        if math.isclose(dist_min_val, 0) and algorithm == MatchingAlgorithm.DEFAULT:
            # If neither result is good by min_val, try to switch to histogram matching
            if dist_hist_val < THRESHOLD_RESULT_DISTANCE:
                # But if the hist_val distance is too low as well, terminate here
                # because we value data correctness rather than guessing
                msg = "Neither template matching nor histogram comparison is accurate enough"
                logger.error(msg)
                raise CannotIdentifyUniqueItem(msg)

            logger.warning("Switching matching algorithm to HISTOGRAM because dist_min_val=0")
            algorithm = MatchingAlgorithm.HISTOGRAM

        match algorithm:
            case MatchingAlgorithm.VARIANTS_ONLY:
                if any(res.template.sockets > 0 for res in results):
                    # Socketable items will always have min_val matching first
                    return min(results, key=lambda res: res.min_val)

                logger.warning("Using VARIANTS_ONLY when sockets=0 defaults to DEFAULT")

            case MatchingAlgorithm.HISTOGRAM:
                return min(results, key=lambda res: res.hist_val)

            case MatchingAlgorithm.DEFAULT:
                return min(results, key=lambda res: res.min_val)

        # Same as DEFAULT
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

        icon = Image.open(item.icon)

        if not item.is_smaller_than_full():
            # TODO: This is a hack to make large items work. Find a better solution.
            icon.thumbnail((100, 200), Image.Resampling.BILINEAR)

        for color in ["r", "g", "b", "w"]:
            for sockets in range(item.sockets, 0, -1):
                # Generate item with sockets in memory
                template = ItemTemplate(
                    image=self.generator.generate_image(icon, item, sockets, color),
                    sockets=sockets,
                )
                variants.append(template)

        return variants

    def check_one(self, image: Image.Image, item: Item) -> MatchResult:
        """Check one screenshot against one item."""
        results = []

        item_variants = self.get_item_variants(item)

        logger.info("Item {} has {} variant(s)", item.name, len(item_variants))

        image = self.crop_out_unique_by_dimensions(image, item)

        if DEBUG:
            self.debug_info.setdefault("cropped_uniques", [])
            self.debug_info["cropped_uniques"].append(image)

        screen = utils.image_to_cv(image)
        hist_base = utils.calc_normalized_histogram(image)

        for template in item_variants:
            if template.image.width > image.width or template.image.height > image.height:
                logger.error(
                    "Template image is larger than unique item: {}x{}px vs {}x{}px",
                    template.image.width,
                    template.image.height,
                    image.width,
                    image.height,
                )
                msg = "Template image is larger than unique item: {}x{}px vs {}x{}px".format(
                    template.image.width,
                    template.image.height,
                    image.width,
                    image.height,
                )
                raise InvalidTemplateDimensions(msg)

            hist = utils.calc_normalized_histogram(template.image)

            hist_val = cv2.compareHist(hist_base, hist, cv2.HISTCMP_BHATTACHARYYA)
            logger.debug("Comparing histograms, hist_val={}", hist_val)

            template_cv = np.array(template.image)
            template_cv = cv2.cvtColor(template_cv, cv2.COLOR_RGBA2GRAY)

            # Match against the screenshot
            result = cv2.matchTemplate(screen, template_cv, cv2.TM_SQDIFF_NORMED)
            min_val, _, min_loc, _ = cv2.minMaxLoc(result)

            logger.debug("Sockets: {}, min_val: {}", template.sockets, min_val)

            match_result = MatchResult(
                item=item,
                loc=min_loc,
                identified=None,
                matched_by=MatchedBy.TEMPLATE_MATCH,
                min_val=min_val,
                hist_val=hist_val,
                template=template,
            )
            results.append(match_result)

        return self.get_best_result(results, MatchingAlgorithm.VARIANTS_ONLY)

    def load_screen(self, screenshot: str | Path) -> np.ndarray:
        """Load a screenshot from file into OpenCV format."""
        screen = cv2.imread(str(screenshot))
        return cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

    def _find_without_resizing(
        self,
        image: Image.Image,
        screen: np.ndarray,
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

        min_val2, min_loc = self._find_without_resizing(self.unique_two_line_cmp, screen)

        logger.debug("Finding unique control start 2 (compressed): min_val={}", min_val2)

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
        self,
        screen: np.ndarray,
        is_identified: bool,
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

            min_val2, min_loc = self._find_without_resizing(self.unique_two_line_end_cmp, screen)

            logger.debug("Finding unique control end 2 (compressed): min_val={}", min_val2)

            if min_val2 <= THRESHOLD_CONTROL:
                return min_loc

            logger.error(
                "Couldn't find unique control end, threshold is {}, line2_min={}",
                THRESHOLD_CONTROL,
                min_val2,
            )
        else:
            min_val1, min_loc = self._find_without_resizing(self.unique_one_line_end, screen)

            logger.debug("Finding unique control end 1: min_val={}", min_val1)

            if min_val1 <= THRESHOLD_CONTROL:
                return min_loc

            logger.error(
                "Couldn't find unique control end, threshold is {}, line1_min={}",
                THRESHOLD_CONTROL,
                min_val1,
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
                ),
            )

        return image

    def find_unique(self, screenshot: str | Path) -> CroppedItemInfo:
        """Return CroppedItemInfo with data about the cropped part of a screenshot."""
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
                    "OPT_ALLOW_NON_FULLHD is disabled and screenshot isn't 1920x1080px, aborting",
                )
                source_screen.close()
                raise NotInFullHD

        res = self._find_unique_control_start(screen)

        if res is None:
            source_screen.close()
            msg = "Unique control guide start not found"
            raise CannotFindUniqueItem(msg)

        min_loc_start, is_identified = res
        min_loc_end = self._find_unique_control_end(screen, is_identified)

        if min_loc_end is None:
            source_screen.close()
            msg = "Unique control guide end not found"
            raise CannotFindUniqueItem(msg)

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
            ),
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
            ),
        )

        source_screen.close()

        base, name = self.title_parser.parse_title(title_img, is_identified=is_identified)

        return CroppedItemInfo(
            image=item_img,
            base=base,
            name=name,
            identified=is_identified,
        )

    def find_item(self, screenshot: str | Path) -> MatchResult:
        """Find an item in a screenshot."""
        logger.info("Finding item in screenshot: {}", screenshot)

        cropped_item = self.find_unique(screenshot)

        if DEBUG:
            self.debug_info["unique_image"] = cropped_item.image
            self.debug_info["results_all"] = []

        if cropped_item.name and OPT_FIND_ITEM_BY_NAME:
            item = self.item_loader.get(cropped_item.name)

            if item.alias:
                logger.warning(
                    "Found aliased item: {}, recording parent: {}",
                    item.name,
                    item.alias,
                )
                item = self.item_loader.get(item.alias)

            logger.success("Found identified item by name")
            return MatchResult(
                item=item,
                loc=(0, 0),
                matched_by=MatchedBy.ITEM_NAME,
                identified=cropped_item.identified,
                min_val=0,
                hist_val=0,
                template=None,
            )

        results_all = []

        filtered_bases = self.item_loader.filter(cropped_item.base)
        logger.info("Searching through {} item base variants", len(filtered_bases))

        if len(filtered_bases) == 1:
            item = filtered_bases[0]
            logger.success("Only one possible unique for base {}", item.base)
            return MatchResult(
                item=item,
                loc=(0, 0),
                matched_by=MatchedBy.ONLY_UNIQUE_FOR_BASE,
                identified=cropped_item.identified,
                min_val=0,
                hist_val=0,
                template=None,
            )

        for item in filtered_bases:
            result = self.check_one(cropped_item.image, item)

            results_all.append(result)

        if DEBUG:
            self.debug_info["results_all"] = results_all

        if cropped_item.base in self.FORCE_HISTOGRAM_MATCHING:
            # Force histogram matching on these bases
            best_result = self.get_best_result(results_all, MatchingAlgorithm.HISTOGRAM)
            best_result.matched_by = MatchedBy.HISTOGRAM_MATCH
        else:
            best_result = self.get_best_result(results_all, MatchingAlgorithm.DEFAULT)

        if best_result.min_val > THRESHOLD_DISCARD and best_result.hist_val == 0:
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

        best_result.identified = cropped_item.identified

        return best_result
