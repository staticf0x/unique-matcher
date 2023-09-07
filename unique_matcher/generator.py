"""Module for generating item sockets."""
import math

from loguru import logger
from PIL import Image

from unique_matcher.constants import ITEM_MAX_SIZE, SOCKET_DIR
from unique_matcher.items import Item

LINK_WIDTH = 17


class ItemGenerator:
    """Generator for item sockets."""

    def __init__(self) -> None:
        self.socket = Image.open(SOCKET_DIR / "socket-src.png")
        self.socket.thumbnail((36, 36), Image.Resampling.BILINEAR)

    def generate_sockets(self, sockets: int, columns: int) -> Image.Image:
        """Generate a socket overlay."""
        if sockets < 1 or sockets > 6:
            raise ValueError("Item can only have 1-6 sockets")

        if columns == 1:
            rows = sockets
        elif columns == 2:
            rows = math.ceil(sockets / 2)

        if sockets == 1:
            columns = 1

        # Blank image
        new_image = Image.new(
            "RGBA",
            (
                columns * self.socket.width + (columns - 1) * LINK_WIDTH,
                rows * self.socket.height + (rows - 1) * LINK_WIDTH,
            ),
        )

        left_offset = 0

        for n in range(sockets):
            if columns == 1:
                col = 0
                row = n
            elif columns == 2:
                col = n % 2
                row = n // 2

            if sockets == 3 and n == 2 and columns == 2:
                # TODO: Hack for middle row for 3 sockets, because the socket
                #       goes to the *right*
                left_offset = self.socket.width + LINK_WIDTH

            offset_x = left_offset + col * (self.socket.width + LINK_WIDTH)
            offset_y = row * (self.socket.height + LINK_WIDTH)

            # Pass the second socket image as a mask to allow transparency
            new_image.paste(self.socket, (offset_x, offset_y), self.socket)

        return new_image

    def generate_image(self, base: Image.Image, item: Item, sockets: int) -> Image.Image:
        """Generate an image of a base item with N sockets."""
        if sockets < 1 or sockets > 6:
            raise ValueError("Item can only have 1-6 sockets")

        # Resize to max size, keep aspect ratio
        base.thumbnail(ITEM_MAX_SIZE, Image.Resampling.BILINEAR)

        if item.is_smaller_than_full():
            logger.debug("Changing item base image dimensions")
            base.thumbnail(
                (
                    int(ITEM_MAX_SIZE[0] * (item.width / 2)),
                    int(ITEM_MAX_SIZE[1] * (item.height / 4)),
                ),
                Image.Resampling.BILINEAR,
            )

        # Prepare new image and paste the item base
        new_image = Image.new("RGBA", base.size)
        new_image.paste(base, (0, 0), base)

        # Generate the socket overlay and place onto the base
        socket_image = self.generate_sockets(sockets, item.cols)
        offset_x = int((base.width - socket_image.width) / 2) + 1
        offset_y = int((base.height - socket_image.height) / 2) + 3

        new_image.paste(socket_image, (offset_x, offset_y), socket_image)

        return new_image
