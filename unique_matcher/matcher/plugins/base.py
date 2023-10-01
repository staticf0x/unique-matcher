"""Base class for matcher plugins."""
from unique_matcher.matcher.items import ItemLoader
from unique_matcher.matcher.result import CroppedItemInfo, MatchResult


class BaseMatcher:
    """Base class for matcher plugins."""

    def __init__(self, item_loader: ItemLoader) -> None:
        self.item_loader = item_loader

    def is_for(self, cropped_item: CroppedItemInfo) -> bool:
        """Return True if this plugin is for cropped_item."""
        raise NotImplementedError

    def match(self, results_all: list[MatchResult], cropped_item: CroppedItemInfo) -> MatchResult:
        """Return the best match for these results."""
        raise NotImplementedError
