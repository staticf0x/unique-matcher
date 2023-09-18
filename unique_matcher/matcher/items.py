"""Item handling."""
import csv
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from loguru import logger

from unique_matcher.constants import ITEM_DIR, OPT_IGNORE_NON_GLOBAL_ITEMS, ROOT_DIR

Color: TypeAlias = Literal["r", "g", "b", "w"]
Colors: Sequence[Color] = ["r", "g", "b", "w"]


@dataclass
class Item:
    """Represent a single item."""

    MAX_WIDTH = 2
    MAX_HEIGHT = 4
    MAX_SOCKETS = 6

    name: str
    file: str
    alias: str
    icon: str | Path
    base: str
    sockets: int = 6
    cols: int = 2
    width: int = 2
    height: int = 4

    def is_smaller_than_full(self) -> bool:
        """Return True if the item is smaller than full dimensions (for cropping)."""
        return self.width < self.MAX_WIDTH or self.height < self.MAX_HEIGHT

    def __hash__(self) -> int:
        """Hash by name (it's unique)."""
        return hash(self.name)


class ItemLoader:
    """Class for loading item data."""

    def __init__(self) -> None:
        self.items: dict[str, Item] = {}

    def load(self) -> None:
        """Load items from CSV."""
        self.items = {}

        with open(ROOT_DIR / "items.csv", newline="") as fread:
            reader = csv.DictReader(fread)

            for row in reader:
                if int(row["enabled"]) == 0:
                    logger.debug("Skipping drop-disabled item: {}", row["name"])
                    continue

                if OPT_IGNORE_NON_GLOBAL_ITEMS and int(row["global"]) == 0:
                    logger.debug("Skipping non-global item: {}", row["name"])
                    continue

                name = row["name"]
                file = row["file"]

                # TODO: Better error handling
                assert (ITEM_DIR / f"{file}.png").exists()

                item = Item(
                    name=name,
                    file=file,
                    alias=row["alias"],
                    icon=ITEM_DIR / f"{file}.png",
                    base=row["base"].replace("'", ""),
                    sockets=int(row["sockets"]),
                    cols=int(row["columns"]),
                    width=int(row["width"] or 2),
                    height=int(row["height"] or 4),
                )
                self.items[file] = item

    def get(self, name: str) -> Item:
        """Find an item by normalized name."""
        return self.items[name]

    def bases(self) -> set[str]:
        """Return a list of all item bases."""
        return {item.base for item in self}

    def filter_(self, base: str) -> list[Item]:
        """Filter items by their base name."""
        return [item for item in self if item.base == base and not item.alias]

    def item_aliases(self, item: Item) -> list[Item]:
        """Get item aliases."""
        return [i for i in self if i.alias == item.file]

    def __iter__(self) -> Iterator[Item]:
        return self.items.values().__iter__()
