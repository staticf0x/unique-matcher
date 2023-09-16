import time

import pyscreenshot
from loguru import logger
from PIL import Image
from PySide6.QtCore import QObject, Slot

from unique_matcher.constants import QUEUE_DIR


class QmlScreenshotter(QObject):
    """Class for grabbing screenshots into the queue folder."""

    def __init__(self) -> None:
        QObject.__init__(self)

    @Slot()
    def grab(self) -> None:
        filename = QUEUE_DIR / f"{time.strftime('%Y-%m-%d-%H-%M-%S')}.png"

        image = pyscreenshot.grab()
        image.save(filename)

        logger.debug(
            "Grabbed a new screenshot: {}",
        )
