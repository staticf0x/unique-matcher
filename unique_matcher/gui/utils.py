"""QML object to handle the matching."""
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from PySide6.QtCore import QObject, Slot

from unique_matcher.constants import DATA_DIR, RESULT_DIR

HELP_URL = "https://github.com/staticf0x/unique-matcher/wiki/Usage"


class QmlUtils(QObject):
    """Utils for use in QML."""

    def __init__(self) -> None:
        QObject.__init__(self)

    @Slot()
    def open_help(self) -> None:
        """Open the help page."""
        webbrowser.open_new_tab(HELP_URL)

    def open_file(self, file: Path) -> None:
        if sys.platform == "win32":
            os.startfile(file)
        elif sys.platform == "darwin":
            subprocess.call(["open", file])
        else:
            subprocess.call(["xdg-open", file])

    @Slot()
    def open_csv(self) -> None:
        self.open_file(RESULT_DIR / sorted(os.listdir(RESULT_DIR))[-1])

    @Slot("QString")
    def open_folder(self, folder) -> None:
        self.open_file(DATA_DIR / folder)
