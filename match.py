#!/usr/bin/env python3
"""Debugging tool for the matching algorithm."""
import argparse
import contextlib
import sys
import tempfile
import webbrowser

import jinja2
from devtools import debug
from loguru import logger
from PIL import Image
from rich.console import Console
from rich.table import Table

from unique_matcher.constants import ROOT_DIR
from unique_matcher.matcher.exceptions import BaseUMError
from unique_matcher.matcher.matcher import THRESHOLD_DISCARD, Matcher

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
    "--show-screenshot",
    action="store_true",
    help="Display the original screenshot",
)
parser.add_argument(
    "--show-unique",
    action="store_true",
    help="Display the unique item used for matching",
)
parser.add_argument("--check-one", type=str, help="Item name to check against")
parser.add_argument("--html", action="store_true", help="Open a debug html page")
args = parser.parse_args()

matcher = Matcher()
result = None

environment = jinja2.Environment(loader=jinja2.FileSystemLoader(ROOT_DIR / "debug"))
template = environment.get_template("debug.html")

if args.show_screenshot:
    Image.open(args.screenshot).show()

if args.check_one:
    result = matcher.check_one(
        matcher.find_unique(args.screenshot).image,
        matcher.item_loader.get(args.check_one),
    )
else:
    with contextlib.suppress(BaseUMError):
        result = matcher.find_item(args.screenshot)

if result and "results_all" in matcher.debug_info:
    table = Table()

    table.add_column("Item")
    table.add_column("Base")
    table.add_column("s/c")
    table.add_column("WxH")
    table.add_column("min_val")
    table.add_column("hist_val")

    if result.item.base in matcher.FORCE_HISTOGRAM_MATCHING:
        sort_lambda = lambda r: r.hist_val  # noqa: E731
    else:
        sort_lambda = lambda r: r.min_val  # noqa: E731

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

    console.print()
    console.print(table)
    console.print()

    if args.html:
        context = {
            "result": result,
            "results_all": sorted(
                matcher.debug_info["results_all"],
                key=lambda r: r.min_val,
            ),
            "screenshot": args.screenshot,
        }

        with tempfile.NamedTemporaryFile("w", delete=False) as unique_image_tmp:
            matcher.debug_info["unique_image"].save(f"{unique_image_tmp.name}.png")
            context["unique_image"] = f"{unique_image_tmp.name}.png"

        if "cropped_uniques" in matcher.debug_info:
            with tempfile.NamedTemporaryFile("w", delete=False) as cropped_unique_tmp:
                matcher.debug_info["cropped_uniques"][0].save(f"{cropped_unique_tmp.name}.png")
                context["cropped_unique"] = f"{cropped_unique_tmp.name}.png"

        if result.template:
            with tempfile.NamedTemporaryFile("w", delete=False) as template_tmp:
                result.template.image.save(f"{template_tmp.name}.png")
                context["template"] = f"{template_tmp.name}.png"

        with open("debug.html", "w") as fwrite:
            fwrite.write(template.render(**context))

        webbrowser.open_new_tab("debug.html")

if result:
    debug(result)

    if args.show_template and result.template:
        result.template.image.show()

if args.show_unique:
    matcher.debug_info["unique_image"].show()

    if "cropped_uniques" in matcher.debug_info:
        matcher.debug_info["cropped_uniques"][0].show()
