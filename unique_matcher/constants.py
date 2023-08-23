"""Constants and configuration."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()

# Directory definitions
ITEM_DIR = ROOT_DIR / "items"
SOCKET_DIR = ROOT_DIR / "socket"

# Other paths
# Path to the image that contains image of an empty socket
SOCKET_ICON_PATH = SOCKET_DIR / "socket.png"

# Maximum size of an item image for comparison
# (might differ from artwork found on wiki)
ITEM_MAX_SIZE: tuple[int, int] = (99, 200)

DEBUG: bool = False

OPT_CROP_SCREEN = False
OPT_EARLY_FOUND = True
