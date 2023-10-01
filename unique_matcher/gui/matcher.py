"""QML object to handle the matching."""
import os
import shutil

from loguru import logger
from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from unique_matcher.constants import DONE_DIR, ERROR_DIR, QUEUE_DIR, RESULT_DIR
from unique_matcher.gui.results import ResultFile
from unique_matcher.matcher.exceptions import BaseUMError
from unique_matcher.matcher.matcher import Matcher, MatchResult
from unique_matcher.matcher.utils import is_csv_empty


class QmlMatcher(QObject):
    """Matcher for use in QML."""

    items_changed = Signal()
    queue_length_changed = Signal()
    processed_length_changed = Signal()
    errors_length_changed = Signal()

    newResult = Signal(dict)  # noqa: N815

    def __init__(self) -> None:
        # Matcher needs to be initiated before the whole QObject,
        # because the QML object try to access it on launch already
        self.matcher = Matcher()

        QObject.__init__(self)

        self.result_file = ResultFile()
        self.result_file.new()
        self._cnt = 1

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_next)
        self.timer.setInterval(250)
        self.timer.start()

        self._errors = []

    @Property(int, notify=items_changed)  # type: ignore[operator, arg-type]
    def items(self) -> int:
        """Return the number of items in the DB."""
        return len(self.matcher.item_loader.items)

    @Property(int, notify=queue_length_changed)  # type: ignore[operator, arg-type]
    def queue_length(self) -> int:
        """Return the size of the queue."""
        return len(os.listdir(QUEUE_DIR))

    @Property(int, notify=processed_length_changed)  # type: ignore[operator, arg-type]
    def processed_length(self) -> int:
        """Return the number of processed screenshots."""
        inside_folders = sum(
            len(os.listdir(DONE_DIR / item)) for item in DONE_DIR.iterdir() if item.is_dir()
        )
        in_root = len([file for file in DONE_DIR.iterdir() if file.is_file()])

        return inside_folders + in_root

    @Property(int, notify=errors_length_changed)  # type: ignore[operator, arg-type]
    def errors_length(self) -> int:
        """Return the number of errors."""
        return len(os.listdir(ERROR_DIR))

    @Slot()
    def process_next(self) -> None:
        """Process one screenshot."""
        if len(os.listdir(QUEUE_DIR)) == 0:
            return

        self.timer.stop()  # This is basically a lock
        file = sorted(os.listdir(QUEUE_DIR))[0]

        try:
            result = self.matcher.find_item(QUEUE_DIR / file)

            self.result_file.add(result)

            self.newResult.emit(
                {
                    "n": self._cnt,
                    "item": result.item.name,
                    "base": result.item.base,
                    "matched_by": str(result.matched_by),
                },
            )
            self._cnt += 1

            # Sort items in done/<item>/...
            item_folder = DONE_DIR.joinpath(result.item.file)
            item_folder.mkdir(exist_ok=True, parents=True)

            shutil.move(QUEUE_DIR / file, item_folder / file)
            self.processed_length_changed.emit()
        except BaseUMError as e:
            self.newResult.emit(
                {
                    "n": self._cnt,
                    "item": "Error",
                    "base": "-",
                    "matched_by": "Couldn't find any item",
                },
            )
            self._cnt += 1

            shutil.move(QUEUE_DIR / file, ERROR_DIR / file)
            self.errors_length_changed.emit()
            logger.exception("Error during processing: {}", str(e))
        except Exception as e:
            if file in self._errors:
                # If the file already failed once to process,
                # mark it as failed and move to errors folder.
                self.newResult.emit(
                    {
                        "n": self._cnt,
                        "item": "Error",
                        "base": "-",
                        "matched_by": "Unexpected error",
                    },
                )
                self._cnt += 1

                shutil.move(QUEUE_DIR / file, ERROR_DIR / file)
                self.errors_length_changed.emit()
                logger.exception("Unexpected error during processing: {}", str(e))

                # No need to store them forever
                self._errors.remove(file)
            else:
                logger.error("Couldn't read file {}, retrying", file)
                self._errors.append(file)

        self.queue_length_changed.emit()
        self.timer.start()

    @Slot()
    def snapshot(self) -> None:
        """Create a new snapshot."""
        self.result_file.snapshot()

    @Slot()
    def reset_result_counter(self) -> None:
        """Reset the internal row counter."""
        self._cnt = 1

    @Slot()
    def cleanup(self) -> None:
        """Remove empty CSVs."""
        logger.debug("Running cleanup")

        for file in RESULT_DIR.iterdir():
            if RESULT_DIR / file == self.result_file.current_file:
                # Do not delete the currently used file
                # This is also the reason why cleanup is here
                # and not in utils, because we have access to result_file
                continue

            if is_csv_empty(RESULT_DIR / file):
                logger.debug("Deleting empty CSV: {}", file.name)

                try:
                    os.remove(RESULT_DIR / file)
                except OSError:
                    logger.error("Cannot delete empty CSV: {}", file.name)
