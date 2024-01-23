import argparse
import os
from collections import Counter

import tabulate
from loguru import logger
from rich.console import Console
from rich.table import Table

from unique_matcher.constants import ROOT_DIR
from unique_matcher.matcher.items import ItemLoader

logger.remove()

EXCLUDED_DATA_SETS = ["non-global", "inventory", "imperial-staff", "example"]
DATA_DIR = ROOT_DIR / "tests" / "test_data" / "contains"


def gather_all_items() -> set[str]:
    """Get a set of all items from all data sets."""
    items = set()

    for data_set in os.listdir(DATA_DIR):
        if data_set in EXCLUDED_DATA_SETS:
            continue

        for item_name in os.listdir(DATA_DIR / data_set):
            items.add(item_name)

    return items


parser = argparse.ArgumentParser()
parser.add_argument("--only-missing", action="store_true")
parser.add_argument("--format", choices=["table", "md"], default="table")

args = parser.parse_args()

item_loader = ItemLoader()
item_loader.load()

# Count all bases in the DB
cnt = Counter([i.base for i in item_loader])

# Group by base
bases = {base: [] for base in item_loader.bases()}

for item_name in gather_all_items():
    item = item_loader.get(item_name)

    bases.setdefault(item.base, [])
    bases[item.base].append(item)

# Print the table
match args.format:
    case "table":
        table = Table()
        table.add_column("Base")
        table.add_column("Found")
        table.add_column("Missing items")

        for base, base_items in sorted(bases.items()):
            found = set(bases[base])
            available = set(item_loader.filter_base(base))
            missing = available - found

            if not args.only_missing or missing:
                table.add_row(
                    base,
                    f"{len(base_items)}/{cnt.get(base)}",
                    ", ".join([it.name for it in missing]),
                )

        console = Console()
        console.print(table)
    case "md":
        table = []

        for base, base_items in sorted(bases.items()):
            found = set(bases[base])
            available = set(item_loader.filter_base(base))
            missing = available - found

            if not args.only_missing or missing:
                table.append(
                    (
                        base,
                        f"{len(base_items)}/{cnt.get(base)}",
                        ", ".join([f"[{it.name}]({it.poewiki_url()})" for it in missing]),
                    ),
                )

        print(
            tabulate.tabulate(table, headers=("Base", "Found", "Missing items"), tablefmt="github")
        )
