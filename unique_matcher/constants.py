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

# If enabled, the Matcher object will gather debug data for later use
DEBUG: bool = True

# Allow screenshots that are not 1920x1080px, it will reduce accuracy
# Default: False
OPT_ALLOW_NON_FULLHD: bool = True

# Enable item name matching for identified items
# Default: True
OPT_FIND_ID_BY_NAME: bool = False

# Ignore non-global drops, i.e. boss drops, metamorph drops, etc.
# Default: True
OPT_IGNORE_NON_GLOBAL_ITEMS: bool = True
