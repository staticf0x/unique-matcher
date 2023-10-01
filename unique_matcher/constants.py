"""Constants and configuration."""
from pathlib import Path

VERSION = "0.5.2"
ROOT_DIR = Path(__file__).parent.parent.resolve()

# Directory definitions
ASSETS_DIR = ROOT_DIR / "assets"
ITEM_DIR = ASSETS_DIR / "items"
SOCKET_DIR = ASSETS_DIR / "socket"
TEMPLATES_DIR = ASSETS_DIR / "templates"

DATA_DIR = ROOT_DIR / "data"
QUEUE_DIR = DATA_DIR / "queue"
ERROR_DIR = DATA_DIR / "errors"
DONE_DIR = DATA_DIR / "done"
LOG_DIR = DATA_DIR / "logs"
RESULT_DIR = DATA_DIR / "results"

TESSERACT_PATH = ROOT_DIR / "Tesseract-OCR" / "tesseract.exe"

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
OPT_FIND_ITEM_BY_NAME: bool = True

# Ignore non-global drops, i.e. boss drops, metamorph drops, etc.
# Default: True
OPT_IGNORE_NON_GLOBAL_ITEMS: bool = True

# Raise an exception if the parsed item name cannot be found in the DB
# WARNING: This is a debugging tool that should be False in production
# Default: False
OPT_FIND_BY_NAME_RAISE: bool = False
