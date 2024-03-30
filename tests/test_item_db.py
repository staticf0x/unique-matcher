"""These tests are for the consistency and validity of the item DB.

The tests actually provide warnings instead of assertions, because
there are some exceptions to what might look like rules and patterns.
"""

import warnings
from pathlib import Path

from PIL import Image


def test_complete_data(item_loader):
    """Test basic item data consistency."""
    for item in item_loader:
        assert item.name
        assert item.file
        assert Path(item.icon).exists()
        assert 1 <= item.width <= item.MAX_WIDTH
        assert 1 <= item.height <= item.MAX_HEIGHT
        assert 0 <= item.sockets <= item.MAX_SOCKETS
        assert 0 <= item.cols <= 2
        assert item.base


def test_item_base_dimensions(item_loader):
    """Test that all items within one base have the same dimension."""
    bases = {}

    # Group items by base
    for item in item_loader:
        bases.setdefault(item.base, [])
        bases[item.base].append(item)

    for base, items in bases.items():
        msg = f"Items from base '{base}' don't have the same dimensions"

        if len({(item.width, item.height) for item in items}) != 1:
            warnings.warn(msg, stacklevel=1)


def test_dimensions_from_image(item_loader):
    """Test that the recorded item dimensions are equal to the image dimension.

    This assumes that 1 slot in the inventory is equal to 78px.
    However, in some cases it is required that the item is recorder to be
    larger, since some parts of the image can be lost and the detection
    accuracy goes down, e.g. Wings of Entropy.
    """
    for item in item_loader:
        img = Image.open(item.icon)

        expected = (round(img.width / 78), round(img.height / 78))
        actual = (item.width, item.height)

        if expected != actual:
            msg = (
                f"Item {item.name} might have wrong dimensions\n"
                f"  Expected from image dimensions: {expected}\n"
                f"  Dimension in the DB:            {actual}"
            )
            warnings.warn(msg, stacklevel=1)

        img.close()
