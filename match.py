import os
import sys

from devtools import debug
from loguru import logger

from unique_matcher.matcher import Matcher

templates: list[tuple] = []
TEMPLATE_DIR = "generated"
SCREENSHOT_DIR = "screenshots"
THRESHOLD = 0.25

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | <level>{level:7s}</level> | {message}",
    level="INFO",
    colorize=True,
)

matcher = Matcher()

for file in sorted(os.listdir(SCREENSHOT_DIR)):
    result = matcher.find_item(os.path.join(SCREENSHOT_DIR, file))

    if result:
        print(f"Found item {result.item.name} in {file}")
