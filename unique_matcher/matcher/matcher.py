"""Module for matching unique items."""
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
    CannotFindUniqueItemError,
    CannotIdentifyUniqueItemError,
    InvalidTemplateDimensionsError,
    NotInFullHDError,
)
from unique_matcher.matcher.generator import ItemGenerator
from unique_matcher.matcher.items import SOCKET_COLORS, Item, ItemLoader
from unique_matcher.matcher.plugins import PluginLoader
from unique_matcher.matcher.result import (
    CroppedItemInfo,
    ItemTemplate,
    MatchedBy,
    MatchingAlgorithm,
    MatchResult,
    get_best_result,
)
from unique_matcher.matcher.title import TitleParser

# Threshold at which we must discard the result because it's inconclusive
# even amongst the already filtered bases.
THRESHOLD_DISCARD = 0.96

# Threshold for the control guides (item title decorations).
# Has to be low enough to not allow other clutter to get in.
# Typically the min_val of guides is ~0.06.
THRESHOLD_CONTROL = 0.16


class Matcher:
    """Main class for matching items in a screenshot."""

    def __init__(self) -> None:
        self.generator = ItemGenerator()
        self.item_loader = ItemLoader()
        self.item_loader.load()
        self.title_parser = TitleParser(self.item_loader)
        self.plugin_loader = PluginLoader(self.item_loader)

        self.unique_one_line = Image.open(str(TEMPLATES_DIR / "unique-one-line-fullhd.png"))
        self.unique_one_line_end = Image.open(str(TEMPLATES_DIR / "unique-one-line-end-fullhd.png"))

        self.unique_two_line = Image.open(str(TEMPLATES_DIR / "unique-two-line-fullhd.png"))
        self.unique_two_line_end = Image.open(str(TEMPLATES_DIR / "unique-two-line-end-fullhd.png"))

        self.unique_two_line_cmp = Image.open(
            str(TEMPLATES_DIR / "unique-two-line-fullhd-compressed.png"),
        )
        self.unique_two_line_end_cmp = Image.open(
            str(TEMPLATES_DIR / "unique-two-line-end-fullhd-compressed.png"),
        )

        self.debug_info: dict[str, Any] = {}

    def get_item_variants(self, item: Item) -> list[ItemTemplate]:
        """Get a list of images for all socket variants of an item."""
        variants = []

        if item.sockets == 0:
            icon = Image.open(item.icon)
            icon.thumbnail(ITEM_MAX_SIZE, Image.Resampling.BILINEAR)

            if item.width != Item.MAX_WIDTH or item.height != Item.MAX_HEIGHT:
                logger.debug("Changing item base image dimensions")
                icon.thumbnail(
                    (
                        int(ITEM_MAX_SIZE[0] * (item.width / Item.MAX_WIDTH)),
                        int(ITEM_MAX_SIZE[1] * (item.height / Item.MAX_HEIGHT)),
                    ),
                    Image.Resampling.BILINEAR,
                )

            return [ItemTemplate(image=icon, sockets=0)]

        icon = Image.open(item.icon)

        if not item.is_smaller_than_full():
            # TODO: This is a hack to make large items work. Find a better solution.
            icon.thumbnail((100, 200), Image.Resampling.BILINEAR)

        for color in SOCKET_COLORS:
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
                raise InvalidTemplateDimensionsError(msg)

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

        return get_best_result(results, MatchingAlgorithm.VARIANTS_ONLY)

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
        *,
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
                raise NotInFullHDError

        res = self._find_unique_control_start(screen)

        if res is None:
            source_screen.close()
            msg = "Unique control guide start not found"
            raise CannotFindUniqueItemError(msg)

        min_loc_start, is_identified = res
        min_loc_end = self._find_unique_control_end(screen, is_identified=is_identified)

        if min_loc_end is None:
            source_screen.close()
            msg = "Unique control guide end not found"
            raise CannotFindUniqueItemError(msg)

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
            logger.info("Found item: {}", item.name)

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

        filtered_bases = self.item_loader.filter_base(cropped_item.base)
        logger.info("Searching through {} item base variants", len(filtered_bases))

        if len(filtered_bases) == 1:
            item = filtered_bases[0]
            logger.success("Only one possible unique for base {}", item.base)
            logger.info("Found item: {}", item.name)

            return MatchResult(
                item=item,
                loc=(0, 0),
                matched_by=MatchedBy.ONLY_UNIQUE_FOR_BASE,
                identified=cropped_item.identified,
                min_val=0,
                hist_val=0,
                template=None,
            )

        # Check all bases
        for item in filtered_bases:
            result = self.check_one(cropped_item.image, item)
            results_all.append(result)

        if DEBUG:
            self.debug_info["results_all"] = results_all

        plugin = self.plugin_loader.load(cropped_item)
        best_result = plugin.match(results_all, cropped_item)

        if best_result.min_val > THRESHOLD_DISCARD and best_result.hist_val == 0:
            logger.error(
                "Couldn't identify a unique item, even the best result "
                "was above THRESHOLD_DISCARD (min_val={})",
                result.min_val,
            )
            raise CannotIdentifyUniqueItemError

        if aliases := self.item_loader.item_aliases(best_result.item):
            logger.warning(
                "Found aliased item: {}, aliases:\n{}",
                best_result.item.name,
                "\n".join([item.name for item in aliases]),
            )

        best_result.identified = cropped_item.identified

        logger.info("Found item: {}", best_result.item.name)

        return best_result
