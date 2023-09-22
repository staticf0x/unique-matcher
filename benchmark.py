"""Run benchmark on testing data sets."""
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.table import Table
from simple_term_menu import TerminalMenu  # type: ignore[import]

from unique_matcher.constants import ROOT_DIR
from unique_matcher.matcher.exceptions import CannotFindUniqueItemError
from unique_matcher.matcher.items import Item
from unique_matcher.matcher.matcher import Matcher

logger.remove()

DATA_DIR = ROOT_DIR / "tests" / "test_data" / "contains"

# Accuracy between 99% and 100% is still acceptable
# but make it stand out by warning.
ACCURACY_WARN_THRESHOLD = 0.99

# These data sets will be excluded from the total count for the wiki page
EXCLUDE_FROM_TOTAL = ["example", "download"]


@dataclass
class SuiteResult:
    """Helper class for storing the result of a single benchmark run."""

    data_set: str
    items: int
    screenshots: int
    found: int
    accuracy: float


class Benchmark:
    """Class for running the whole benchmark suite."""

    def __init__(self, *, display: bool = True) -> None:
        self.matcher = Matcher()
        self.to_benchmark: list[Item] = []
        self._report: list[bool] = []
        self._times: list[float] = []
        self.console = Console()
        self.table = Table()
        self.display = display

        self.table.add_column("#")
        self.table.add_column("Item")
        self.table.add_column("Identified")
        self.table.add_column("Found")
        self.table.add_column("Matched by")
        self.table.add_column("Time (ms)")
        self.table.add_column("min_val")

    def add(self, name: str) -> None:
        """Add item to benchmark suite."""
        item = self.matcher.item_loader.get(name)
        self.to_benchmark.append(item)

    def _get_test_set(self, name: str) -> list[Path]:
        """Return the screenshot test set for an item."""
        return sorted(DATA_DIR.joinpath(self.data_set, name).iterdir())

    def report(self, found: bool) -> None:  # noqa: FBT001
        """Add report (whether the item was correctly identified) for a single test."""
        self._report.append(found)

    def _run_one(self, item: Item) -> None:
        """Run benchmark for one item."""
        test_set = self._get_test_set(item.file)

        for screen in test_set:
            t_start = time.perf_counter()

            try:
                result = self.matcher.find_item(screen)

                found = result.item == item
            except CannotFindUniqueItemError:
                found = False

            t_end = time.perf_counter()

            if found:
                self.table.add_row(
                    str(len(self._times) + 1),
                    item.name,
                    "Yes" if result.identified else "No",
                    "[green]Yes[/green]",
                    str(result.matched_by),
                    f"{(t_end - t_start) * 1e3:.2f}",
                    f"{result.min_val:.3f}" if result.min_val > 0 else "-",
                )
            else:
                self.table.add_row(
                    str(len(self._times) + 1),
                    item.name,
                    "-",
                    "[red]No[/red]",
                    "-",
                    f"{(t_end - t_start) * 1e3:.2f}",
                )

            self.report(found)
            self._times.append((t_end - t_start) * 1e3)

    def run(self, data_set: str) -> None:
        """Run the whole benchmark suite."""
        self._report = []
        self._times = []
        self.data_set = data_set

        # Load all screenshots
        for name in sorted(os.listdir(DATA_DIR / self.data_set)):
            self.add(name)

        # Run the benchmark
        for item in track(self.to_benchmark, description=f"Benchmarking {data_set}"):
            self._run_one(item)

        found = sum(self._report)
        total = len(self._report)
        accuracy = found / total

        # Draw the result table
        if self.display:
            self.console.print(self.table)

            if math.isclose(accuracy, 1):
                color = "green"
            elif accuracy > ACCURACY_WARN_THRESHOLD:
                color = "yellow"
            else:
                color = "red"

            lines = [
                f"Data set:    {data_set}",
                f"Items:       {len(self.to_benchmark)}",
                f"Screenshots: {total}",
                f"Found:       {found}",
                f"Accuracy:    [bold {color}]{accuracy:.2%}[/bold {color}]",
                "",
                f"Average time: {np.mean(self._times):6.2f} ms",
                f"Fastest:      {np.min(self._times):6.2f} ms",
                f"Slowest:      {np.max(self._times):6.2f} ms",
                f"Std:          {np.std(self._times):6.2f} ms",
            ]

            panel = Panel("\n".join(lines), title="Summary")
            self.console.print(panel)

        return SuiteResult(
            data_set=data_set,
            items=len(self.to_benchmark),
            screenshots=total,
            found=found,
            accuracy=accuracy,
        )


def run() -> None:
    """Run the benchmark."""
    data_sets = sorted(os.listdir(DATA_DIR))

    # Make the user choose a data set
    menu = TerminalMenu(
        data_sets,
        multi_select=True,
        show_multi_select_hint=True,
    )
    choices = menu.show()

    if choices is None:
        return

    run_multiple = len(choices) > 1

    results: list[SuiteResult] = []

    for choice in choices:
        benchmark = Benchmark(display=not run_multiple)
        result = benchmark.run(data_sets[choice])
        results.append(result)

    if run_multiple:
        # Display a table used for the wiki page
        print()
        print("| Data set      | Items | Screenshots | Found | Accuracy    |")
        print("| ------------- | ----- | ----------- | ----- | ----------- |")

        for res in results:
            if res.data_set in EXCLUDE_FROM_TOTAL:
                continue

            print(
                f"| {res.data_set:<13s} | {res.items:<5d} | {res.screenshots:<11d} | {res.found:<5d} | {res.accuracy:<11.2%} |"
            )

        total_items = sum(res.items for res in results if res.data_set not in EXCLUDE_FROM_TOTAL)
        total_found = sum(res.found for res in results if res.data_set not in EXCLUDE_FROM_TOTAL)
        total_screenshots = sum(
            res.screenshots for res in results if res.data_set not in EXCLUDE_FROM_TOTAL
        )
        total_accuracy = total_found / total_screenshots

        print(
            f"| **Total**     | {total_items:<5d} | {total_screenshots:<11d} | {total_found:<5d} | **{total_accuracy:.2%}** |"
        )


if __name__ == "__main__":
    run()
