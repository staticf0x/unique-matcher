import os
import shutil

from loguru import logger
from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from unique_matcher.constants import DONE_DIR, ERROR_DIR, QUEUE_DIR
from unique_matcher.gui.results import ResultFile
from unique_matcher.matcher.exceptions import BaseUMError
from unique_matcher.matcher.matcher import Matcher


class QmlMatcher(QObject):
    """Matcher for use in QML."""

    items_changed = Signal()
    queue_length_changed = Signal()
    processed_length_changed = Signal()
    errors_length_changed = Signal()

    newResult = Signal(dict)

    def __init__(self) -> None:
        # Matcher needs to be initiated before the whole QObject,
        # because the QML object try to access it on launch already
        self.matcher = Matcher()

        QObject.__init__(self)

        self._results = []
        self.result_file = ResultFile()
        self.result_file.new()
        self._cnt = 1

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_next)
        self.timer.setInterval(250)
        self.timer.start()

    @Property("int", notify=items_changed)
    def items(self) -> int:
        """Return the number of items in the DB."""
        return len(self.matcher.item_loader.items)

    @Property(int, notify=queue_length_changed)
    def queue_length(self) -> int:
        """Return the size of the queue."""
        return len(os.listdir(QUEUE_DIR))

    @Property(int, notify=processed_length_changed)
    def processed_length(self) -> int:
        """Return the number of processed screenshots."""
        return len(os.listdir(DONE_DIR))

    @Property(int, notify=errors_length_changed)
    def errors_length(self) -> int:
        """Return the number of errors."""
        return len(os.listdir(ERROR_DIR))

    @Slot()
    def process_next(self) -> None:
        """Process one screenshot."""
        if self.queue_length == 0:
            return

        file = os.listdir(QUEUE_DIR)[0]

        try:
            result = self.matcher.find_item(QUEUE_DIR / file)

            self.result_file.add(result)

            self._results.append(result)  # This is used for export
            self.newResult.emit(
                {
                    "n": self._cnt,
                    "item": result.item.name,
                    "base": result.item.base,
                    "matched_by": str(result.matched_by),
                },
            )
            self._cnt += 1

            shutil.move(QUEUE_DIR / file, DONE_DIR / file)
            self.processed_length_changed.emit()
        except BaseUMError as e:
            shutil.move(QUEUE_DIR / file, ERROR_DIR / file)
            self.errors_length_changed.emit()
            logger.exception("Error during processing: {}", str(e))

        self.queue_length_changed.emit()

    @Slot()
    def snapshot(self) -> None:
        """Create a new snapshot."""
        self.result_file.snapshot()
