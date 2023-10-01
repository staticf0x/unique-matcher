"""Module for everything related to match results."""
import math
from dataclasses import dataclass
from enum import Enum

from loguru import logger
from PIL import Image

from unique_matcher.matcher.exceptions import CannotIdentifyUniqueItemError
from unique_matcher.matcher.items import Item

# Threshold for discarding results based on the distance
# in either min_val or hist_val between the best result
# and the second best result.
# If the distance is too low (lower than THRESHOLD_RESULT_DISTANCE),
# the result will be discarded for the detection not being accurate enough.
THRESHOLD_RESULT_DISTANCE = 0.02


@dataclass
class CroppedItemInfo:
    """Helper class for the cropped out part with unique item info."""

    image: Image.Image
    base: str
    name: str
    identified: bool


class MatchingAlgorithm(Enum):
    """Enum for matching algorithm during get_best_result."""

    DEFAULT = 0
    VARIANTS_ONLY = 1
    HISTOGRAM = 2


@dataclass
class ItemTemplate:
    """Helper class for the image template."""

    image: Image.Image
    sockets: int


class MatchedBy(Enum):
    """How the item was matched."""

    TEMPLATE_MATCH = 0
    HISTOGRAM_MATCH = 1
    ONLY_UNIQUE_FOR_BASE = 2
    ITEM_NAME = 3
    SOLARIS_CIRCLET = 4

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
            case self.SOLARIS_CIRCLET:
                return "Solaris Circlet plugin"
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


def get_distance_from_best(results: list[MatchResult]) -> tuple[float, float]:
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
    results: list[MatchResult],
    algorithm: MatchingAlgorithm = MatchingAlgorithm.DEFAULT,
) -> MatchResult:
    """Find the best result (min(min_val) or min(hist_val))."""
    logger.debug("Matching algorithm: {}", algorithm)

    dist_min_val, dist_hist_val = get_distance_from_best(results)

    if math.isclose(dist_min_val, 0) and algorithm == MatchingAlgorithm.DEFAULT:
        # If neither result is good by min_val, try to switch to histogram matching
        if dist_hist_val < THRESHOLD_RESULT_DISTANCE:
            # But if the hist_val distance is too low as well, terminate here
            # because we value data correctness rather than guessing
            msg = "Neither template matching nor histogram comparison is accurate enough"
            logger.error(msg)
            raise CannotIdentifyUniqueItemError(msg)

        logger.warning("Switching matching algorithm to HISTOGRAM because dist_min_val=0")
        algorithm = MatchingAlgorithm.HISTOGRAM

    match algorithm:
        case MatchingAlgorithm.VARIANTS_ONLY:
            if any(res.template.sockets > 0 for res in results):  # type: ignore[union-attr]
                # Socketable items will always have min_val matching first
                # NOTE: Ignoring union-attr because mypy doesn't know that
                #       with VARIANTS_ONLY the template is *always* present
                return min(results, key=lambda res: res.min_val)

            logger.warning("Using VARIANTS_ONLY when sockets=0 defaults to DEFAULT")

        case MatchingAlgorithm.HISTOGRAM:
            return min(results, key=lambda res: res.hist_val)

        case MatchingAlgorithm.DEFAULT:
            return min(results, key=lambda res: res.min_val)

    # Same as DEFAULT
    return min(results, key=lambda res: res.min_val)
