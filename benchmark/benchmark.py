import os
from pathlib import Path

import rich
from devtools import Timer
from loguru import logger
from texttable import Texttable

from unique_matcher.matcher import ITEM_DIR, THRESHOLD, Item, Matcher

logger.remove()

BENCH_DIR = Path(__file__).parent.resolve()


def _get_item(name: str, sockets: int = 6) -> Item:
    """Get an Item object for item name."""
    return Item(
        name=name,
        icon=os.path.join(ITEM_DIR, f"{name}.png"),
        sockets=sockets,
    )


def _get_test_set(name: str) -> list[str]:
    """Return the screenshot test set for an item."""
    files = []

    for file in sorted(os.listdir(os.path.join(BENCH_DIR, "screenshots", name))):
        files.append(os.path.join(BENCH_DIR, "screenshots", name, file))

    return files


def benchmark_item(matcher: Matcher, name: str, sockets: int = 6) -> None:
    """Run a benchmark for a single item."""
    item = _get_item(name, sockets)
    print(f"\n=== {item.name} ===")

    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.add_row(["Screenshot", "min_val", "Found", "Time (ms)"])
    table.set_cols_dtype(["t", "f", "t", lambda v: f"{v:.1f}"])

    results_all = []

    for screen in _get_test_set(name):
        with Timer(verbose=False) as timer:
            result = matcher.check_one(matcher.load_screen(screen), item)
            results_all.append(result)

        table.add_row(
            [
                os.path.basename(screen),
                result.min_val,
                "Yes" if result.min_val <= THRESHOLD else "No",
                timer.results[0].elapsed() * 1e3,
            ]
        )

    print(table.draw())

    if any(result.found() for result in results_all):
        found = "[green]Yes[/green]"
    else:
        found = "[red]No[/red]"

    rich.print(f"\nFound: {found}")


def run() -> None:
    """Run the benchmark."""
    matcher = Matcher()
    benchmark_item(matcher, "Bramblejack", 6)
    benchmark_item(matcher, "Briskwrap", 6)
    benchmark_item(matcher, "Bereks_Grip", 0)
    benchmark_item(matcher, "Bereks_Pass", 0)
    benchmark_item(matcher, "Bereks_Respite", 0)
    benchmark_item(matcher, "Chernobogs_Pillar", 6)
    benchmark_item(matcher, "Dusktoe", 4)
    benchmark_item(matcher, "Mindspiral", 4)
    benchmark_item(matcher, "Ngamahus_Flame", 6)
    benchmark_item(matcher, "Nomics_Storm", 4)


if __name__ == "__main__":
    run()
