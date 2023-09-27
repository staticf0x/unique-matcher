"""Verification tool for items processed by Unique Matcher.

Use this to interactively verify data/done items and move them int
tests/test_data/contains/gathered.
"""
import shutil
import sys

import rich
from loguru import logger
from PIL import Image
from simple_term_menu import TerminalMenu  # type: ignore[import]

from unique_matcher.constants import DONE_DIR, ERROR_DIR, ROOT_DIR
from unique_matcher.matcher.matcher import Matcher

DATA_SET = ROOT_DIR / "tests" / "test_data" / "contains" / "gathered"

logger.remove()

matcher = Matcher()

for item_dir in sorted(DONE_DIR.iterdir()):
    if item_dir.is_file():
        continue

    for screenshot in (DONE_DIR / item_dir).iterdir():
        file = DONE_DIR / item_dir / screenshot

        item_name = file.parent.name
        item = matcher.item_loader.get(item_name)

        with Image.open(item.icon) as image:
            image.show()

        cropped = matcher.find_unique(file)
        cropped.image.show()

        rich.print(f"\n[bold]{item.name}[/bold]")
        rich.print(f"[link={item.poewiki_url()}]PoE wiki[/link]")

        print()

        menu = TerminalMenu(["[y] yes", "[n] no"], title="Is this item correct? (Ctrl+C to exit)")
        choice_idx = menu.show()

        if choice_idx is None:
            sys.exit()

        if choice_idx == 0:
            target_dir = DATA_SET / item_dir.name
            target_dir.mkdir(parents=True, exist_ok=True)

            target = target_dir / screenshot.name

            if target.exists():
                rich.print("[bold red]Target already exist![/bold red]")
                continue

            print(f"Move:\n  source: {file}\n  dest:   {target}")
            shutil.move(file, target)
        else:
            target_dir = ERROR_DIR
            target = target_dir / screenshot.name

            print(f"Move:\n  source: {file}\n  dest:   {target}")
            shutil.move(file, target)

        if len(list((DONE_DIR / item_dir).iterdir())) == 0:
            (DONE_DIR / item_dir).rmdir()
