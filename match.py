import argparse
import sys

from devtools import debug
from loguru import logger
from PIL import Image
from rich.console import Console
from rich.table import Table

from unique_matcher.matcher import THRESHOLD_DISCARD, Matcher

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
parser.add_argument(
    "--show-screenshot", action="store_true", help="Display the original screenshot"
)
parser.add_argument("--check-one", type=str, help="Item name to check against")
parser.add_argument("--all", action="store_true", help="Display all results, not only the best one")
args = parser.parse_args()

matcher = Matcher()

if args.show_screenshot:
    Image.open(args.screenshot).show()

if args.check_one:
    result = matcher.check_one(
        Image.open(args.screenshot),
        matcher.item_loader.get(args.check_one),
    )
else:
    result = matcher.find_item(args.screenshot)

if args.all:
    table = Table()

    table.add_column("Item")
    table.add_column("Base")
    table.add_column("s/c")
    table.add_column("WxH")
    table.add_column("min_val")

    for i, res in enumerate(sorted(matcher.debug_info["results_all"], key=lambda r: r.min_val)):
        style = None

        if i == 0:
            style = "green"

        if res.min_val > THRESHOLD_DISCARD:
            style = "red"

        table.add_row(
            res.item.name,
            res.item.base,
            f"{res.item.sockets}/{res.item.cols}",
            f"{res.item.width}x{res.item.height}",
            f"{res.min_val:.3f}",
            style=style,
        )

    console = Console()

    print()
    console.print(table)
    print()

debug(result)

if args.show_template:
    result.template.image.show()
