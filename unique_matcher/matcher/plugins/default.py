from unique_matcher.matcher.plugins.base import BaseMatcher
from unique_matcher.matcher.result import (
    CroppedItemInfo,
    MatchingAlgorithm,
    MatchResult,
    get_best_result,
)


class DefaultMatcher(BaseMatcher):
    """Default matcher for most items."""

    def is_for(self, cropped_item: CroppedItemInfo) -> bool:
        # This is for all items by default, so always return True
        return True

    def match(self, results_all: list[MatchResult], cropped_item: CroppedItemInfo) -> MatchResult:
        return get_best_result(results_all, MatchingAlgorithm.DEFAULT)
