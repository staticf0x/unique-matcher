import numpy as np

from unique_matcher.matcher.plugins.base import BaseMatcher
from unique_matcher.matcher.result import (
    CroppedItemInfo,
    MatchedBy,
    MatchingAlgorithm,
    MatchResult,
    get_best_result,
)

AVG_COLOR: int = 100


class SolarisCircletMatcher(BaseMatcher):
    """Matcher for Flamesight, Thundersight and Galesight."""

    def is_for(self, cropped_item: CroppedItemInfo) -> bool:
        return cropped_item.base == "Solaris Circlet"

    def match(self, results_all: list[MatchResult], cropped_item: CroppedItemInfo) -> MatchResult:
        best_result = get_best_result(results_all, MatchingAlgorithm.DEFAULT)

        if best_result.item.file in ["Flamesight", "Galesight", "Thundersight"]:
            gem = cropped_item.image.crop((25, 45, 32, 50))
            arr = np.array(gem)

            avg_colors = arr.mean(axis=0).mean(axis=0)[:3]

            if (
                avg_colors[0] > AVG_COLOR
                and avg_colors[1] < AVG_COLOR
                and avg_colors[2] < AVG_COLOR
            ):
                return MatchResult(
                    item=self.item_loader.get("Flamesight"),
                    loc=(0, 0),
                    matched_by=MatchedBy.SOLARIS_CIRCLET,
                    identified=cropped_item.identified,
                    min_val=0,
                    hist_val=0,
                    template=None,
                )

            if (
                avg_colors[0] < AVG_COLOR
                and avg_colors[1] < AVG_COLOR
                and avg_colors[2] > AVG_COLOR
            ):
                return MatchResult(
                    item=self.item_loader.get("Galesight"),
                    loc=(0, 0),
                    matched_by=MatchedBy.SOLARIS_CIRCLET,
                    identified=cropped_item.identified,
                    min_val=0,
                    hist_val=0,
                    template=None,
                )

            if (
                avg_colors[0] > AVG_COLOR
                and avg_colors[1] > AVG_COLOR
                and avg_colors[2] < AVG_COLOR
            ):
                return MatchResult(
                    item=self.item_loader.get("Thundersight"),
                    loc=(0, 0),
                    matched_by=MatchedBy.SOLARIS_CIRCLET,
                    identified=cropped_item.identified,
                    min_val=0,
                    hist_val=0,
                    template=None,
                )

        return best_result
