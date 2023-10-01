"""Module for handling the result CSV files from GUI."""
import csv
import time
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pathlib import Path

from loguru import logger

from unique_matcher.constants import RESULT_DIR
from unique_matcher.matcher.matcher import MatchResult


class ResultFile:
    """Handle writing results."""

    HEADER: ClassVar[list[str]] = [
        "item",
        "count",
    ]

    def __init__(self) -> None:
        self.current_file: Path | None = None
        RESULT_DIR.mkdir(exist_ok=True, parents=True)

    def new(self) -> None:
        """Create a new CSV."""
        filename = RESULT_DIR / f"{time.strftime('%Y-%m-%d-%H-%M-%S')}.csv"
        self.current_file = filename

        with open(filename, "w", newline="", encoding="utf-8") as fwrite:
            writer = csv.DictWriter(fwrite, self.HEADER)
            writer.writeheader()

        logger.info("Created new result CSV: {}", self.current_file)

    def _load(self) -> dict[str, int]:
        """Load data from current CSV."""
        logger.debug("Loading CSV")

        if not self.current_file:
            raise ValueError

        with open(self.current_file, newline="", encoding="utf-8") as fread:
            reader = csv.DictReader(fread)

            return {row["item"]: int(row["count"]) for row in reader}

    def _save(self, data: dict[str, int]) -> None:
        """Write data into current CSV."""
        logger.debug("Writing CSV")

        if not self.current_file:
            raise ValueError

        with open(self.current_file, "w", newline="", encoding="utf-8") as fwrite:
            writer = csv.DictWriter(fwrite, self.HEADER)
            writer.writeheader()

            for item, count in sorted(data.items(), key=lambda v: v[1], reverse=True):
                writer.writerow({"item": item, "count": str(count)})

    def add(self, result: MatchResult) -> None:
        """Add one match result to the current CSV."""
        current_data = self._load()

        current_data.setdefault(result.item.name, 0)
        current_data[result.item.name] += 1

        self._save(current_data)

    def snapshot(self) -> None:
        """Create new CSV file."""
        logger.info("Creating new snapshot")
        self.new()
