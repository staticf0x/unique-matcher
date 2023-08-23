import os
import time
from pathlib import Path

import rich
from loguru import logger
from texttable import Texttable

from unique_matcher.items import Item, ItemLoader
from unique_matcher.matcher import THRESHOLD, Matcher

logger.remove()

BENCH_DIR = Path(__file__).parent.resolve()


class Benchmark:
    """Class for running the whole benchmark suite."""

    def __init__(self):
        self.matcher = Matcher()
        self.item_loader = ItemLoader()
        self.item_loader.load()
        self.to_benchmark: list[Item] = []

    def add(self, name: str) -> None:
        """Add item to benchmark suite."""
        item = self.item_loader.get(name)
        self.to_benchmark.append(item)

    def _get_test_set(self, name: str) -> list[str]:
        """Return the screenshot test set for an item."""
        files = []

        for file in sorted(os.listdir(BENCH_DIR / "screenshots" / name)):
            files.append(BENCH_DIR / "screenshots" / name / file)

        return files

    def _run_one(self, item: Item) -> None:
        """Run benchmark for one item."""
        print(f"\n=== {item.name} ===")

        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.add_row(["Screenshot", "min_val", "Found", "Time (ms)"])
        table.set_cols_dtype(["t", "f", "t", lambda v: f"{v:.1f}"])

        results_all = []

        for screen in self._get_test_set(item.name):
            t_start = time.perf_counter()
            result = self.matcher.check_one(self.matcher.load_screen(screen), item)
            t_end = time.perf_counter()

            results_all.append(result)

            table.add_row(
                [
                    screen.name,
                    result.min_val,
                    "Yes" if result.min_val <= THRESHOLD else "No",
                    (t_end - t_start) * 1e3,
                ]
            )

        print(table.draw())

        if any(result.found() for result in results_all):
            found = "[green]Yes[/green]"
        else:
            found = "[red]No[/red]"

        rich.print(f"\nFound: {found}")

    def run(self) -> None:
        """Run the whole benchmark suite."""
        for item in self.to_benchmark:
            self._run_one(item)


def run() -> None:
    """Run the benchmark."""
    benchmark = Benchmark()
    benchmark.add("Bramblejack")
    benchmark.add("Briskwrap")
    benchmark.add("Bereks_Grip")
    benchmark.add("Bereks_Pass")
    benchmark.add("Bereks_Respite")
    benchmark.add("Chernobogs_Pillar")
    benchmark.add("Dusktoe")
    benchmark.add("Mindspiral")
    benchmark.add("Ngamahus_Flame")
    benchmark.add("Nomics_Storm")
    benchmark.add("Fencoil")
    benchmark.add("Death_and_Taxes")
    benchmark.run()


if __name__ == "__main__":
    run()
