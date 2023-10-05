from typing import ClassVar

from unique_matcher.matcher.plugins.base import BaseMatcher
from unique_matcher.matcher.result import (
    CroppedItemInfo,
    MatchedBy,
    MatchingAlgorithm,
    MatchResult,
    get_best_result,
)


class HistogramMatcher(BaseMatcher):
    """Matcher for items when histogram comparison is necessary."""

    ALLOW_BASES: ClassVar[list[str]] = [
        "Two-Stone Ring",
    ]

    def is_for(self, cropped_item: CroppedItemInfo) -> bool:
        return cropped_item.base in self.ALLOW_BASES

    def match(self, results_all: list[MatchResult], cropped_item: CroppedItemInfo) -> MatchResult:
        best_result = get_best_result(results_all, MatchingAlgorithm.HISTOGRAM)
        best_result.matched_by = MatchedBy.HISTOGRAM_MATCH

        return best_result
