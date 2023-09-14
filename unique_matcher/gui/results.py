import csv
import os
import time
from typing import ClassVar

from devtools import debug
from loguru import logger

from unique_matcher.constants import RESULT_DIR
from unique_matcher.matcher.matcher import MatchResult


class ResultFile:
    """Handle writing results."""

    HEADER: ClassVar[list[str]] = [
        "item",
        "count",
    ]

    def __init__(self):
        self.current_file: str | None = None
        os.makedirs(RESULT_DIR, exist_ok=True)

    def new(self) -> None:
        """Create a new CSV."""
        filename = RESULT_DIR / f"{time.strftime('%Y-%m-%d-%H-%M-%S')}.csv"
        self.current_file = filename

        with open(filename, "w") as fwrite:
            writer = csv.DictWriter(fwrite, self.HEADER)
            writer.writeheader()

        logger.info("Created new result CSV: {}", self.current_file)

    def _load(self) -> dict[str, int]:
        """Load data from current CSV."""
        logger.debug("Loading CSV")

        with open(self.current_file, "r", newline="") as fread:
            reader = csv.DictReader(fread)

            return {row["item"]: int(row["count"]) for row in reader}

    def _save(self, data: dict[str, int]) -> None:
        """Write data into current CSV."""
        logger.debug("Writing CSV")

        with open(self.current_file, "w", newline="") as fwrite:
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
