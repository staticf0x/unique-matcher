import argparse
import csv

from rich.console import Console
from rich.table import Table

parser = argparse.ArgumentParser()
parser.add_argument("action", type=str, choices=["list", "edit"])

list_group = parser.add_argument_group("list")
list_group.add_argument("--enabled", action="store_true", help="Only list enabled items")
list_group.add_argument("--disabled", action="store_true", help="Only list disabled items")
list_group.add_argument("--base", type=str, help="Filter item base")
list_group.add_argument(
    "--no-sc", action="store_true", help="Only list items without sockets/columns"
)
list_group.add_argument("--no-wh", action="store_true", help="Only list items without width/height")
list_group.add_argument(
    "--global", dest="yes_global", action="store_true", help="Only list items that can drop"
)
list_group.add_argument("--no-global", action="store_true", help="Hide items that can drop")

edit_group = parser.add_argument_group("edit")
edit_group.add_argument("--set-width", type=int, help="Width to set")
edit_group.add_argument("--set-height", type=int, help="Height to set")
edit_group.add_argument("--set-sockets", type=int, help="Sockets to set")
edit_group.add_argument("--set-columns", type=int, help="Columns to set")
edit_group.add_argument("--set-enabled", type=int, help="1 to enable, 0 to disable")

args = parser.parse_args()

fread = open("items.csv")
reader = csv.DictReader(fread)


def filtered(line: dict) -> bool:
    if args.enabled and line["enabled"] == "0":
        return False

    if args.disabled and line["enabled"] == "1":
        return False

    if args.base and args.base not in line["base"]:
        return False

    if args.no_sc and not (line["sockets"] == "0" or line["columns"] == "0"):
        return False

    if args.no_wh and not (line["width"] == "" or line["height"] == ""):
        return False

    if args.yes_global and line["global"] == "0":
        return False

    if args.no_global and line["global"] == "1":
        return False

    return True


if args.action == "list":
    table = Table()

    table.add_column("Item")
    table.add_column("File")
    table.add_column("Alias")
    table.add_column("Base")
    table.add_column("s/c")
    table.add_column("WxH")
    table.add_column("Enabled")
    table.add_column("Global")

    for line in reader:
        if not filtered(line):
            continue

        table.add_row(
            line["name"],
            line["file"],
            line["alias"],
            line["base"],
            f"{line['sockets']}/{line['columns']}",
            f"{line['width']}x{line['height']}",
            "Yes" if line["enabled"] == "1" else "No",
            "Yes" if line["global"] == "1" else "No",
        )

    console = Console()

    console.print(table)
    print()
    print(f"Count: {len(table.rows)}")

if args.action == "edit":
    fwrite = open("items-new.csv", "w")
    writer = csv.DictWriter(
        fwrite,
        [
            "name",
            "file",
            "alias",
            "sockets",
            "columns",
            "base",
            "enabled",
            "global",
            "width",
            "height",
        ],
    )
    writer.writeheader()

    for line in reader:
        if filtered(line):
            if args.set_width:
                line["width"] = str(args.set_width)

            if args.set_height:
                line["height"] = str(args.set_height)

            if args.set_sockets:
                line["sockets"] = str(args.set_sockets)

            if args.set_columns:
                line["columns"] = str(args.set_columns)

            if args.set_enabled:
                line["enabled"] = str(args.set_enabled)

        writer.writerow(line)

    fread.close()
