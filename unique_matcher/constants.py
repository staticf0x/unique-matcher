"""Constants and configuration."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()

# Directory definitions
ITEM_DIR = ROOT_DIR / "items"
SOCKET_DIR = ROOT_DIR / "socket"
TEMPLATES_DIR = ROOT_DIR / "templates"

# Maximum size of an item image for comparison
# (might differ from artwork found on wiki)
ITEM_MAX_SIZE: tuple[int, int] = (104, 208)

DEBUG: bool = False

OPT_ALLOW_NON_FULLHD = True
