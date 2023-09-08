import argparse
import sys

from devtools import debug
from loguru import logger
from PIL import Image

from unique_matcher.matcher import Matcher

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level:7s}</level> | {message}",
    level="DEBUG",
    colorize=True,
)

parser = argparse.ArgumentParser()
parser.add_argument("screenshot", type=str, help="Path to the screenshot")
parser.add_argument(
    "--show-template",
    action="store_true",
    help="Display the item template that was used to match the item",
)
parser.add_argument("--check-one", type=str, help="Item name to check against")
args = parser.parse_args()

matcher = Matcher()

if args.check_one:
    result = matcher.check_one(
        Image.open(args.screenshot),
        matcher.item_loader.get(args.check_one),
    )
else:
    result = matcher.find_item(args.screenshot)

debug(result)

if args.show_template:
    result.template.image.show()
