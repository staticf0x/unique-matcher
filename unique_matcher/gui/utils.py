"""QML object to handle the matching."""
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

from PySide6.QtCore import QObject, Slot

from unique_matcher.constants import DATA_DIR, DONE_DIR, RESULT_DIR

HELP_URL = "https://github.com/staticf0x/unique-matcher/wiki/Usage"
ISSUE_URL = "https://github.com/staticf0x/unique-matcher/issues/new/choose"
CHANGELOG_URL = "https://github.com/staticf0x/unique-matcher/blob/master/CHANGELOG.md"


class QmlUtils(QObject):
    """Utils for use in QML."""

    def __init__(self) -> None:
        QObject.__init__(self)

    @Slot()
    def open_help(self) -> None:
        """Open the help page."""
        webbrowser.open_new_tab(HELP_URL)

    @Slot()
    def open_changelog(self) -> None:
        """Open the changelog."""
        webbrowser.open_new_tab(CHANGELOG_URL)

    @Slot()
    def report_issue(self) -> None:
        """Open the issue reporting on GitHub."""
        webbrowser.open_new_tab(ISSUE_URL)

    def open_file(self, file: Path) -> None:
        """Use OS's way to open a file or directory."""
        if sys.platform == "win32":
            os.startfile(file)
        elif sys.platform == "darwin":
            subprocess.call(["open", file])
        else:
            subprocess.call(["xdg-open", file])

    @Slot()
    def open_csv(self) -> None:
        """Open the folder with CSV results."""
        self.open_file(RESULT_DIR / sorted(os.listdir(RESULT_DIR))[-1])

    @Slot("QString")
    def open_folder(self, folder: str) -> None:
        """Open a single folder."""
        self.open_file(DATA_DIR / folder)

    @Slot()
    def zip_done(self) -> None:
        """Zip the done folder and open the directory where the zip file is."""
        shutil.make_archive(DATA_DIR / "TestDataSet", "zip", DATA_DIR, DONE_DIR.name)
        self.open_file(DATA_DIR)
