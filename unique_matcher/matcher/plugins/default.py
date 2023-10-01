from loguru import logger

from unique_matcher.matcher.exceptions import CannotIdentifyUniqueItemError
from unique_matcher.matcher.plugins.base import BaseMatcher
from unique_matcher.matcher.result import (
    CroppedItemInfo,
    MatchingAlgorithm,
    MatchResult,
    get_best_result,
)

# Threshold at which we must discard the result because it's inconclusive
# even amongst the already filtered bases.
THRESHOLD_DISCARD = 0.96


class DefaultMatcher(BaseMatcher):
    """Default matcher for most items."""

    def is_for(self, cropped_item: CroppedItemInfo) -> bool:
        # This is for all items by default, so always return True
        return True

    def match(self, results_all: list[MatchResult], cropped_item: CroppedItemInfo) -> MatchResult:
        best_result = get_best_result(results_all, MatchingAlgorithm.DEFAULT)

        if best_result.min_val > THRESHOLD_DISCARD:
            logger.error(
                "Couldn't identify a unique item, even the best result "
                "was above THRESHOLD_DISCARD (min_val={})",
                best_result.min_val,
            )
            raise CannotIdentifyUniqueItemError

        return best_result
