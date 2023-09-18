"""Run benchmark on testing data sets."""
import math
import os
import time
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


class Benchmark:
    """Class for running the whole benchmark suite."""

    def __init__(self) -> None:
        self.matcher = Matcher()
        self.to_benchmark: list[Item] = []
        self._report: list[bool] = []
        self._times: list[float] = []
        self.console = Console()
        self.table = Table()

        self.table.add_column("#")
        self.table.add_column("Item")
        self.table.add_column("Identified")
        self.table.add_column("Found")
        self.table.add_column("Matched by")
        self.table.add_column("Time (ms)")

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

        for name in sorted(os.listdir(DATA_DIR / self.data_set)):
            self.add(name)

        for item in track(self.to_benchmark, description="Gathering results"):
            self._run_one(item)

        # Draw the result table
        self.console.print(self.table)

        found = sum(self._report)
        total = len(self._report)
        accuracy = found / total

        if math.isclose(accuracy, 1):
            color = "green"
        elif accuracy > ACCURACY_WARN_THRESHOLD:
            color = "yellow"
        else:
            color = "red"

        lines = [
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


def run() -> None:
    """Run the benchmark."""
    benchmark = Benchmark()

    data_sets = sorted(os.listdir(DATA_DIR))

    # Make the user choose a data set
    menu = TerminalMenu(data_sets)
    choice_idx = menu.show()

    benchmark.run(data_sets[choice_idx])


if __name__ == "__main__":
    run()
