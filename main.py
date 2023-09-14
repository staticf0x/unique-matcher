import sys

from loguru import logger
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType

from unique_matcher.constants import LOG_DIR, VERSION
from unique_matcher.gui import QML_PATH
from unique_matcher.gui.matcher import QmlMatcher
from unique_matcher.gui.screenshot import QmlScreenshotter

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
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()

    # Properties
    engine.rootContext().setContextProperty("VERSION", VERSION)

    qmlRegisterType(QmlMatcher, "Matcher", 1, 0, "Matcher")
    qmlRegisterType(QmlScreenshotter, "Screenshotter", 1, 0, "Screenshotter")

    engine.load(QML_PATH / "main.qml")  # Load main window

    if not engine.rootObjects():
        sys.exit(-1)

    exit_code = app.exec()
    del engine
    sys.exit(exit_code)
