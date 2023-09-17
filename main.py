import os
import sys

from jinja2 import BaseLoader, Environment
from loguru import logger
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType

from unique_matcher.constants import (
    DONE_DIR,
    ERROR_DIR,
    LOG_DIR,
    QUEUE_DIR,
    ROOT_DIR,
    VERSION,
)
from unique_matcher.gui import QML_PATH
from unique_matcher.gui.matcher import QmlMatcher

AHK_TEMPLATE = """#s::
{
    Run "screen.exe", "{{ root }}", "Hide"
}"""

CONFIG_TEMPLATE = """[screenshot]
screen = 0
"""

if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level:7s}</level> | {message}",
        level="DEBUG",
        colorize=True,
    )
    logger.add(
        LOG_DIR / "matcher.log",
        rotation="10 MB",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level:7s}</level> | {message}",
        level="DEBUG",
    )

    # Create all working dirs
    for path in [DONE_DIR, ERROR_DIR, QUEUE_DIR, LOG_DIR]:
        os.makedirs(path, exist_ok=True)

    # Create the AHK script
    if not os.path.exists(ROOT_DIR / "screenshot.ahk"):
        template = Environment(loader=BaseLoader).from_string(AHK_TEMPLATE)
        rendered = template.render(root=ROOT_DIR)

        with open(ROOT_DIR / "screenshot.ahk", "w", newline="\r\n") as fwrite:
            fwrite.write(rendered)

    # Create config if it doesn't exist
    if not os.path.exists(ROOT_DIR / "config.ini"):
        template = Environment(loader=BaseLoader).from_string(CONFIG_TEMPLATE)
        rendered = template.render(root=ROOT_DIR)

        with open(ROOT_DIR / "config.ini", "w", newline="\r\n") as fwrite:
            fwrite.write(rendered)

    # Init app
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # Properties
    engine.rootContext().setContextProperty("VERSION", VERSION)

    qmlRegisterType(QmlMatcher, "Matcher", 1, 0, "Matcher")  # type: ignore[call-overload]

    engine.load(QML_PATH / "main.qml")  # Load main window

    if not engine.rootObjects():
        sys.exit(-1)

    exit_code = app.exec()
    del engine
    sys.exit(exit_code)
