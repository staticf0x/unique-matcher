import os
from dataclasses import dataclass

import cv2
import numpy as np
from loguru import logger

from unique_matcher.constants import ROOT_DIR
from unique_matcher.generator import ItemGenerator

THRESHOLD = 0.3
ITEM_DIR = ROOT_DIR / "items"


@dataclass
class Item:
    name: str
    icon: str
    sockets: int = 6


@dataclass
class MatchResult:
    item: Item
    loc: tuple[int, int]
    min_val: float

    def found(self) -> bool:
        return self.min_val <= THRESHOLD

    @property
    def confidence(self) -> float:
        """Turn min_val into percentage confidence."""
        if self.found():
            return 100.0

        return -100 / (1 - THRESHOLD) * (self.min_val - THRESHOLD) + 100


class Matcher:
    def __init__(self) -> None:
        self.generator = ItemGenerator()
        self.items = self.load_items()

    def load_items(self):
        items = []

        for file in sorted(os.listdir(ITEM_DIR)):
            item = Item(
                name=file.replace(".png", ""),
                icon=os.path.join(ITEM_DIR, file),
            )
            items.append(item)

        return items

    def get_best_result(self, results: list[MatchResult]) -> MatchResult:
        return min(results, key=lambda res: res.min_val)

    def check_one(self, screen: np.ndarray, item: Item) -> MatchResult:
        results = []

        if item.sockets > 0:
            for sockets in range(item.sockets, 0, -1):
                # Generate item with sockets in memory
                template = self.generator.generate_image(item.icon, sockets)
                template = np.array(template)
                template = cv2.cvtColor(template, cv2.COLOR_RGBA2GRAY)

                # Match against the screenshot
                result = cv2.matchTemplate(screen, template, cv2.TM_SQDIFF_NORMED)
                min_val, _, min_loc, _ = cv2.minMaxLoc(result)

                match_result = MatchResult(item, min_loc, min_val)

                if match_result.found():
                    # Optimization, sort of... We're only interested in finding
                    # the item itself, not how many sockets it has, so it's
                    # fine to return early
                    logger.success(
                        "Found item {} early, sockets={}, min_val={}",
                        match_result.item.name,
                        sockets,
                        match_result.min_val,
                    )
                    return match_result

                results.append(match_result)

            # If we couldn't find the item immediately, return the best result
            # This is useful mainly for benchmarking and tests
            return self.get_best_result(results)

        template = cv2.imread(item.icon)
        template = cv2.cvtColor(template, cv2.COLOR_RGBA2GRAY)

        # Match against the screenshot
        result = cv2.matchTemplate(screen, template, cv2.TM_SQDIFF_NORMED)
        min_val, _, min_loc, _ = cv2.minMaxLoc(result)

        return MatchResult(item, min_loc, min_val)

    def load_screen(self, screenshot: str) -> np.ndarray:
        screen = cv2.imread(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

        return screen

    def find_item(self, screenshot: str) -> MatchResult | None:
        screen = self.load_screen(screenshot)

        for item in self.items:
            result = self.check_one(screen, item)

            if result.found():
                logger.success(
                    "Found item {} in {}, min_val={}", result.item.name, screenshot, result.min_val
                )

                return result

        return None
