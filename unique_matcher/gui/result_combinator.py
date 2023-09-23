"""Module for combining the result CSVs in QML."""
import csv
import sys
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot

from unique_matcher.constants import RESULT_DIR


class QmlResultCombinator(QObject):
    """Class for combining result CSVs."""

    resultsLoaded = Signal(list, arguments=["files"])  # noqa: N815
    previewLoaded = Signal(list, arguments=["items"])  # noqa: N815
    combinedChanged = Signal(list, arguments=["items"])  # noqa: N815

    def __init__(self) -> None:
        QObject.__init__(self)

    def get_combined_results(self, files: list[Path]) -> list[dict[str, str | int]]:
        """Get a list of combined results, sorted by count."""
        combined = {}

        for file in files:
            with open(RESULT_DIR / file, newline="") as fread:
                reader = csv.DictReader(fread)

                for item in reader:
                    combined.setdefault(item["item"], 0)
                    combined[item["item"]] += int(item["count"])

        return [
            {"item": v[0], "count": v[1]}
            for v in sorted(
                combined.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        ]

    @Slot()
    def load_results(self) -> None:
        """Load CSV list."""
        files = []

        for n, file in enumerate(sorted(RESULT_DIR.iterdir())):
            with open(RESULT_DIR / file, newline="") as fread:
                reader = csv.DictReader(fread)

                if len(list(reader)) == 0:
                    # Skip empty CSVs
                    continue

            row = {"n": n, "checked": False, "file": file.name}
            files.append(row)

        logger.debug("Loaded {} result CSVs", len(files))

        self.resultsLoaded.emit(files)

    @Slot(str)
    def load_preview(self, file: str) -> None:
        """Load a preview of one CSV."""
        logger.debug("Loading preview for {}", file)

        with open(RESULT_DIR / file, newline="") as fread:
            reader = csv.DictReader(fread)

            self.previewLoaded.emit(list(reader))

    @Slot(list)
    def combine_results(self, files: list[str]) -> None:
        """Combine selected files."""
        logger.debug("Combining results of {} CSVs", len(files))

        self.combinedChanged.emit(self.get_combined_results(files))

    @Slot(list, str)
    def save_combined(self, files: list[str], output: str) -> None:
        """Write the combined CSV into user selected file."""
        if sys.platform == "win32":
            output_path = Path(output.replace("file://", "").lstrip("/"))
        else:
            output_path = Path(output.replace("file://", ""))

        logger.info("Saving combined CSV into {}", str(output_path))

        combined_results = self.get_combined_results(files)

        with output_path.open("w", newline="") as fwrite:
            writer = csv.DictWriter(fwrite, ["item", "count"])
            writer.writeheader()

            for row in combined_results:
                writer.writerow(row)
