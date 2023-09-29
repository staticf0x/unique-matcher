import configparser
import os
import sys

from jinja2 import Environment
from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot

from unique_matcher.constants import ROOT_DIR

CONFIG_TEMPLATE = """[screenshot]
screen = -1
shortcut = Win+S
"""

AHK_TEMPLATE = """{{ shortcut }}::
{
    Run "screen.exe", "{{ root }}", "Hide"
}"""

MOD_KEY_LUT = {
    "Win": "#",
    "Alt": "!",
    "Ctrl": "^",
    "Shift": "+",
    "Altgr": "<^>!",
}

KEY_LUT = {
    "MouseL": "LButton",
    "MouseR": "RButton",
    "MouseM": "MButton",
    "Mouse4": "XButton1",
    "Mouse5": "XButton2",
}


def create_config():
    """Create the default config.ini."""
    if ROOT_DIR.joinpath("config.ini").exists():
        return

    template = Environment().from_string(CONFIG_TEMPLATE)
    rendered = template.render(root=ROOT_DIR)

    with open(ROOT_DIR / "config.ini", "w", newline="\r\n") as fwrite:
        fwrite.write(rendered)

    logger.info("Created new config.ini")


def load_config():
    """Load config.ini."""
    parser = configparser.ConfigParser()
    parser.read(ROOT_DIR / "config.ini")

    return parser


def shortcut_to_ahk(shortcut: str) -> str:
    """Format config.ini shortcut (<mod key>+<key>) to AHK format."""
    if "+" not in shortcut:
        return KEY_LUT.get(shortcut, shortcut)

    parts = shortcut.split("+")

    mod_key = parts[0]
    key = parts[1]

    return f"{MOD_KEY_LUT[mod_key]}{KEY_LUT.get(key, key)}"


def create_ahk_script(*, overwrite: bool = False) -> None:
    """Create new AHK script."""
    if ROOT_DIR.joinpath("screenshot.ahk").exists() and not overwrite:
        return

    cfg = load_config()
    shortcut = cfg.get("screenshot", "shortcut", fallback="win+s")

    template = Environment().from_string(AHK_TEMPLATE)
    rendered = template.render(root=ROOT_DIR, shortcut=shortcut_to_ahk(shortcut))

    with open(ROOT_DIR / "screenshot.ahk", "w", newline="\r\n") as fwrite:
        fwrite.write(rendered)

    logger.info("Created new screenshot.ahk")


class QmlConfig(QObject):
    """Class for managing config.ini from QML."""

    shortcutLoaded = Signal(str, str, arguments="mod_key,key")

    def __init__(self) -> None:
        QObject.__init__(self)

    @Slot(str, str)
    def change_shortcut(self, mod_key: str, key: str) -> None:
        """Change shortcut in config.ini and update the AHK script."""
        shortcut = key if mod_key == "None" else f"{mod_key}+{key}"

        logger.info("Setting screenshot shortcut to {}", shortcut)

        cfg = load_config()
        cfg.set("screenshot", "shortcut", shortcut)

        with open(ROOT_DIR / "config.ini", "w") as fwrite:
            cfg.write(fwrite)

        create_ahk_script(overwrite=True)

    @Slot()
    def load_current(self) -> None:
        """Load current shortcut and emit shortcutLoaded."""
        cfg = load_config()
        shortcut = cfg.get("screenshot", "shortcut", fallback="Win+S")

        if "+" in shortcut:
            mod_key, key = shortcut.split("+")

            self.shortcutLoaded.emit(mod_key, key)
        else:
            self.shortcutLoaded.emit("None", shortcut)

    @Slot()
    def restart_ahk(self) -> None:
        """Restart the AHK script."""
        if sys.platform == "win32":
            logger.info("Restarting AHK script")
            os.startfile(ROOT_DIR / "screenshot.ahk")
        else:
            logger.warning("Restarting AHK script is not supported on {}", sys.platform)
