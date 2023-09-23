"""Main GUI application."""

import sys

from loguru import logger
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType

from unique_matcher.constants import DONE_DIR, ERROR_DIR, LOG_DIR, QUEUE_DIR, VERSION
from unique_matcher.gui import QML_PATH, config
from unique_matcher.gui.config import QmlConfig
from unique_matcher.gui.matcher import QmlMatcher
from unique_matcher.gui.result_combinator import QmlResultCombinator
from unique_matcher.gui.utils import QmlUtils

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
        path.mkdir(exist_ok=True, parents=True)

    # Create config if it doesn't exist
    config.create_config()

    # Create the AHK script
    config.create_ahk_script()

    # Init app
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # Properties
    engine.rootContext().setContextProperty("VERSION", VERSION)

    qmlRegisterType(QmlMatcher, "Matcher", 1, 0, "Matcher")  # type: ignore[call-overload]
    qmlRegisterType(QmlUtils, "Utils", 1, 0, "Utils")  # type: ignore[call-overload]
    qmlRegisterType(QmlConfig, "Config", 1, 0, "Config")  # type: ignore[call-overload]
    qmlRegisterType(QmlResultCombinator, "ResultCombinator", 1, 0, "ResultCombinator")  # type: ignore[call-overload]

    engine.load(QML_PATH / "main.qml")  # Load main window

    if not engine.rootObjects():
        sys.exit(-1)

    exit_code = app.exec()
    del engine
    sys.exit(exit_code)
