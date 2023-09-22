"""Module for combining the result CSVs in QML."""
import csv

from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot

from unique_matcher.constants import RESULT_DIR


class QmlResultCombinator(QObject):
    """Class for combining result CSVs."""

    resultsLoaded = Signal(list, arguments=["files"])
    previewLoaded = Signal(list, arguments=["items"])
    combinedChanged = Signal(list, arguments=["items"])

    def __init__(self) -> None:
        QObject.__init__(self)

    @Slot()
    def load_results(self) -> None:
        """Load CSV list."""
        files = [
            {"n": n, "checked": False, "file": file.name}
            for n, file in enumerate(sorted(list(RESULT_DIR.iterdir())))
        ]

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

        combined = {}

        for file in files:
            with open(RESULT_DIR / file, newline="") as fread:
                reader = csv.DictReader(fread)

                for item in reader:
                    combined.setdefault(item["item"], 0)
                    combined[item["item"]] += int(item["count"])

        combined_list = [
            {"item": v[0], "count": v[1]}
            for v in sorted(
                combined.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        ]

        self.combinedChanged.emit(combined_list)
