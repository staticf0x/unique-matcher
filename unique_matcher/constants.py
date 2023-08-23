"""Constants and configuration."""
from pathlib import Path

# Path to the image that contains image of an empty socket
SOCKET_ICON_PATH: str = "socket/socket.png"

# Maximum size of an item image for comparison
# (might differ from artwork found on wiki)
ITEM_MAX_SIZE: tuple[int, int] = (99, 200)

ROOT_DIR = Path(__file__).parent.parent.resolve()

DEBUG: bool = True
