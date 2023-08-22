import math

from loguru import logger
from PIL import Image

from unique_matcher.constants import ITEM_MAX_SIZE, SOCKET_ICON_PATH

SPACE = 18
OFFSET_LEFT = 6
OFFSET_TOP = 6


class ItemGenerator:
    """Generator for item sockets."""

    def __init__(self) -> None:
        self.socket = Image.open(SOCKET_ICON_PATH)

    def generate_image(self, base: str, sockets: int) -> Image:
        """Generate an image of a base item with N sockets."""
        if sockets < 1 or sockets > 6:
            raise ValueError("Item can only have 1-6 sockets")

        base = Image.open(base)

        # Resize to max size
        base.thumbnail(ITEM_MAX_SIZE, Image.Resampling.BICUBIC)

        new_image = Image.new("RGBA", base.size)
        new_image.paste(base, (0, 0), base)

        rows = math.ceil(sockets / 2)

        left_offset = 0

        if sockets == 1:
            left_offset = int(ITEM_MAX_SIZE[0] / 2 - self.socket.width / 2 - OFFSET_LEFT)

        match rows:
            case 1:
                top_offset = self.socket.height + SPACE
            case 2:
                top_offset = int((ITEM_MAX_SIZE[1] - 2 * OFFSET_TOP - 2 * self.socket.height) / 3)
            case 3:
                top_offset = 0

        for n in range(sockets):
            col = n % 2
            row = n // 2

            logger.debug("Adding socket {}, row={}, col={}", n + 1, row, col)

            if sockets == 3 and n == 2:
                left_offset = self.socket.width + SPACE + 1

            offset_x = left_offset + OFFSET_LEFT + col * (1 + self.socket.width + SPACE)
            offset_y = top_offset + OFFSET_TOP + row * (1 + self.socket.height + SPACE)
            logger.debug("Offset: [{}, {}]", offset_x, offset_y)

            # Pass the second socket image as a mask to allow transparency
            new_image.paste(self.socket, (offset_x, offset_y), self.socket)

        return new_image
