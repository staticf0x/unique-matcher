"""Item handling."""
import csv
from dataclasses import dataclass
from pathlib import Path

from unique_matcher.constants import ITEM_DIR, ROOT_DIR


@dataclass
class Item:
    """Represent a single item."""

    name: str
    icon: str | Path
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
                name = row["name"]

                # TODO: Better error handling
                assert (ITEM_DIR / f"{name}.png").exists()

                item = Item(
                    name=name,
                    icon=ITEM_DIR / f"{name}.png",
                    sockets=int(row["sockets"]),
                    cols=int(row["columns"]),
                )
                self.items[name] = item

    def get(self, name: str) -> Item:
        return self.items[name]

    def __iter__(self):
        return self.items.values().__iter__()
