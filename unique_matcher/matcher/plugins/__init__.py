from loguru import logger

from unique_matcher.matcher.items import ItemLoader
from unique_matcher.matcher.plugins.base import BaseMatcher
from unique_matcher.matcher.plugins.default import DefaultMatcher
from unique_matcher.matcher.plugins.histogram import HistogramMatcher
from unique_matcher.matcher.plugins.solaris_circlet import SolarisCircletMatcher
from unique_matcher.matcher.result import CroppedItemInfo


class PluginLoader:
    """Helper for loading and picking the correct plugin."""

    def __init__(self, item_loader: ItemLoader) -> None:
        # The order is important, the default matcher must be the last one
        self.plugins = [
            SolarisCircletMatcher(item_loader),
            HistogramMatcher(item_loader),
            DefaultMatcher(item_loader),
        ]

    def load(self, cropped_item: CroppedItemInfo) -> BaseMatcher:
        """Load the correct plugin for the item."""
        for plugin in self.plugins:
            if plugin.is_for(cropped_item):
                logger.info("Using matcher plugin: {}", plugin.__class__.__name__)
                return plugin

        logger.info("Using matcher plugin: {}", self.plugins[-1].__class__.__name__)

        # If there's no special plugin for the item, return the default one
        return self.plugins[-1]
