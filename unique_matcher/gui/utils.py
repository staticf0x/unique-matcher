"""QML object to handle the matching."""
import webbrowser

from PySide6.QtCore import QObject, Slot

HELP_URL = "https://github.com/staticf0x/unique-matcher/wiki/Usage"


class QmlUtils(QObject):
    """Utils for use in QML."""

    def __init__(self) -> None:
        QObject.__init__(self)

    @Slot()
    def open_help(self) -> None:
        """Open the help page."""
        webbrowser.open_new_tab(HELP_URL)
