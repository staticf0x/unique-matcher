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
args = parser.parse_args()

matcher = Matcher()
result = None

if args.show_screenshot:
    Image.open(args.screenshot).show()

if args.check_one:
    result = matcher.check_one(
        matcher.find_unique(args.screenshot)[0],
        matcher.item_loader.get(args.check_one),
    )
else:
    result = matcher.find_item(args.screenshot)

if result and matcher.debug_info.get("results_all"):
    table = Table()

    table.add_column("Item")
    table.add_column("Base")
    table.add_column("s/c")
    table.add_column("WxH")
    table.add_column("min_val")
    table.add_column("hist_val")

    if any(res.hist_val for res in matcher.debug_info["results_all"]):
        sort_lambda = lambda r: r.hist_val
    else:
        sort_lambda = lambda r: r.min_val

    for i, res in enumerate(sorted(matcher.debug_info["results_all"], key=sort_lambda)):
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
            f"{res.hist_val:.3f}",
            style=style,
        )

    console = Console()

    print()
    console.print(table)
    print()

if result:
    debug(result)

    if args.show_template:
        result.template.image.show()

