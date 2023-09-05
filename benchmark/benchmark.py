import os
import time
from pathlib import Path

import numpy as np
import rich
from loguru import logger
from texttable import Texttable

from unique_matcher.exceptions import CannotFindUniqueItem
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
        self._report = []
        self._times = []

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

    def report(self, found: int, total: int) -> None:
        self._report.append((found, total))

    def _run_one(self, item: Item) -> None:
        """Run benchmark for one item."""
        print(f"\n=== {item.name} ===")

        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.add_row(["Screenshot", "min_val", "Found", "Time (ms)"])
        table.set_cols_dtype(["t", "f", "t", lambda v: f"{v:.1f}"])

        results_all = []
        test_set = self._get_test_set(item.file)

        for screen in test_set:
            t_start = time.perf_counter()
            try:
                result = self.matcher.check_one(
                    self.matcher.find_unique(screen)[0],
                    item,
                )
            except CannotFindUniqueItem:
                continue

            t_end = time.perf_counter()
            results_all.append(result)

            table.add_row(
                [
                    screen.name,
                    result.min_val,
                    "Yes" if result.item == item else "No",
                    (t_end - t_start) * 1e3,
                ]
            )

            self._times.append((t_end - t_start) * 1e3)

        # Add to global report
        self.report(sum(result.item == item for result in results_all), len(test_set))

        # Draw the result table
        print(table.draw())

        if any(result.item == item for result in results_all):
            found = "[green]Yes[/green]"
        else:
            found = "[red]No[/red]"

        rich.print(f"\nFound: {found}")

    def run(self) -> None:
        """Run the whole benchmark suite."""
        self._report = []
        self._times = []

        for item in self.to_benchmark:
            self._run_one(item)

        found = sum(res[0] for res in self._report)
        total = sum(res[1] for res in self._report)

        print("\n***** Summary *****")
        print(f"Found:    {found}")
        print(f"Tests:    {total}")
        print(f"Accuracy: {found/total:.2%}")

        print()
        print(f"Average time: {np.mean(self._times):6.2f} ms")
        print(f"Fastest:      {np.min(self._times):6.2f} ms")
        print(f"Slowest:      {np.max(self._times):6.2f} ms")
        print(f"Std:          {np.std(self._times):6.2f} ms")


def run() -> None:
    """Run the benchmark."""
    benchmark = Benchmark()

    for name in sorted(os.listdir(BENCH_DIR / "screenshots")):
        if name.startswith("_"):
            # Skip underscored items to help development
            # if they're misbehaving
            continue

        benchmark.add(name)

    benchmark.run()


if __name__ == "__main__":
    run()
