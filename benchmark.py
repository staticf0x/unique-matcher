"""Run benchmark on testing data sets."""
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from multiprocessing import cpu_count
from pathlib import Path

import numpy as np
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table
from simple_term_menu import TerminalMenu  # type: ignore[import]

from unique_matcher.constants import ROOT_DIR
from unique_matcher.matcher.exceptions import CannotFindUniqueItemError
from unique_matcher.matcher.items import Item, ItemLoader
from unique_matcher.matcher.matcher import Matcher, MatchResult

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
    item_names: set


@dataclass
class CheckResult:
    """A result of a single check (1 item in 1 screenshot)."""

    item: Item
    found: bool
    elapsed: float
    result: MatchResult | None = None


def _run_one(item: Item, test_set: list[Path]) -> list[CheckResult]:
    """Run benchmark for one item on a list of screenshots.

    This must be a function because if it was a class method,
    then ProcessPoolExecutor will not be able to pickle it.
    """
    results = []

    # Matcher is not thread-safe so we need one per worker
    matcher = Matcher()

    for screen in test_set:
        t_start = time.perf_counter()

        try:
            result = matcher.find_item(screen)
            t_end = time.perf_counter()

            res = CheckResult(
                item=item,
                found=result.item == item,
                elapsed=t_end - t_start,
                result=result,
            )
        except CannotFindUniqueItemError:
            t_end = time.perf_counter()
            res = CheckResult(
                item=item,
                found=False,
                elapsed=t_end - t_start,
            )

        results.append(res)

    return results


class Benchmark:
    """Class for running the whole benchmark suite."""

    def __init__(self, *, display: bool = True) -> None:
        self.matcher = Matcher()
        self.to_benchmark: list[Item] = []
        self._report: list[bool] = []
        self._times: list[float] = []
        self.console = Console()
        self.display = display

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

    def print_result_table(self, results: list[CheckResult]) -> None:
        """Print the results."""
        table = Table()
        table.add_column("#")
        table.add_column("Item")
        table.add_column("Identified")
        table.add_column("Found")
        table.add_column("Matched by")
        table.add_column("Time (ms)")
        table.add_column("min_val")

        for n, result in enumerate(results, 1):
            if result.found:
                table.add_row(
                    str(n),
                    result.item.name,
                    "Yes" if result.result.identified else "No",
                    "[green]Yes[/green]",
                    str(result.result.matched_by),
                    f"{result.elapsed * 1e3:.2f}",
                    f"{result.result.min_val:.3f}" if result.result.min_val > 0 else "-",
                )
            else:
                table.add_row(
                    str(n),
                    result.item.name,
                    "-",
                    "[red]No[/red]",
                    "-",
                    f"{result.elapsed * 1e3:.2f}",
                    "-",
                )

        self.console.print(table)

    def run(self, data_set: str) -> None:
        """Run the whole benchmark suite."""
        self._report = []
        self._times = []
        self.data_set = data_set

        # Load all screenshots
        for name in sorted(os.listdir(DATA_DIR / self.data_set)):
            self.add(name)

        with ProcessPoolExecutor(max_workers=min(cpu_count(), 8)) as executor:
            futures = []

            for item in self.to_benchmark:
                f = executor.submit(_run_one, item, self._get_test_set(item.file))
                futures.append(f)

            with Progress() as progress:
                task = progress.add_task(f"Benchmarking {data_set}", total=len(futures))

                while True:
                    completed = sum(f.done() for f in futures)
                    progress.update(task, completed=completed)

                    if completed == len(futures):
                        break

                    time.sleep(0.1)

        all_results = []

        for result in [f.result() for f in futures]:
            all_results.extend(result)

        found = sum(result.found for result in all_results)
        total = len(all_results)
        times = [result.elapsed for result in all_results]
        accuracy = found / total

        # Draw the result table
        if self.display:
            self.print_result_table(all_results)

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
                f"Average time: {np.mean(times)*1e3:6.2f} ms",
                f"Fastest:      {np.min(times)*1e3:6.2f} ms",
                f"Slowest:      {np.max(times)*1e3:6.2f} ms",
                f"Std:          {np.std(times)*1e3:6.2f} ms",
            ]

            panel = Panel("\n".join(lines), title="Summary")
            self.console.print(panel)

        return SuiteResult(
            data_set=data_set,
            items=len(self.to_benchmark),
            screenshots=total,
            found=found,
            accuracy=accuracy,
            item_names={item.file for item in self.to_benchmark},
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
    _il = ItemLoader()
    _il.load()
    items_in_db = len(_il.items)

    for choice in choices:
        benchmark = Benchmark(display=not run_multiple)
        result = benchmark.run(data_sets[choice])
        results.append(result)

    if run_multiple:
        # Display a table used for the wiki page
        print()
        print("| Data set      | Items | Coverage | Screenshots | Found | Accuracy    |")
        print("| ------------- | ----- | -------- | ----------- | ----- | ----------- |")

        tested_items = set()

        for res in results:
            if res.data_set in EXCLUDE_FROM_TOTAL:
                continue

            tested_items |= res.item_names

            columns = [
                f"{res.data_set:<13s}",
                f"{res.items:<5d}",
                f"{res.items/items_in_db:<8.2%}",
                f"{res.screenshots:<11d}",
                f"{res.found:<5d}",
                f"{res.accuracy:<11.2%}",
            ]

            print(f"| {' | '.join(columns)} |")

        total_items = len(tested_items)
        total_found = sum(res.found for res in results if res.data_set not in EXCLUDE_FROM_TOTAL)
        total_screenshots = sum(
            res.screenshots for res in results if res.data_set not in EXCLUDE_FROM_TOTAL
        )
        total_accuracy = total_found / total_screenshots

        columns = [
            "**Total**    ",
            f"{total_items:<5d}",
            f"{total_items/items_in_db:<8.2%}",
            f"{total_screenshots:<11d}",
            f"{total_found:<5d}",
            f"**{total_accuracy:.2%}**" + " " if total_accuracy < 1 else "",
        ]

        print(f"| {' | '.join(columns)} |")


if __name__ == "__main__":
    run()
