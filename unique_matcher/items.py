"""Item handling."""
import csv
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from unique_matcher.constants import ITEM_DIR, ROOT_DIR


@dataclass
class Item:
    """Represent a single item."""

    name: str
    file: str
    icon: str | Path
    base: str
    sockets: int = 6
    cols: int = 2


class ItemLoader:
    """Class for loading item data."""

    def __init__(self) -> None:
        self.items: dict[str, Item] = {}

    def load(self) -> None:
        """Load items from CSV."""
        self.items = {}

        with open(ROOT_DIR / "items.csv") as fread:
            reader = csv.DictReader(fread)

            for row in reader:
                if int(row["enabled"]) == 0:
                    logger.debug("Skipping drop-disabled item: {}", row["name"])
                    continue

                name = row["name"]
                file = row["file"]

                # TODO: Better error handling
                assert (ITEM_DIR / f"{file}.png").exists()

                item = Item(
                    name=name,
                    file=file,
                    icon=ITEM_DIR / f"{file}.png",
                    base=row["base"],
                    sockets=int(row["sockets"]),
                    cols=int(row["columns"]),
                )
                self.items[file] = item

    def get(self, name: str) -> Item:
        """Find an item by normalized name."""
        return self.items[name]

    def bases(self) -> set[str]:
        """Return a list of all item bases."""
        return {item.base for item in self}

    def filter(self, base: str) -> list[Item]:
        """Filter items by their base name."""
        return [item for item in self if item.base == base]

    def __iter__(self):
        return self.items.values().__iter__()
