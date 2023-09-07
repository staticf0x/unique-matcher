"""Various utility functions."""

import cv2
import numpy as np
from PIL import Image


def image_to_cv(image: Image.Image) -> np.ndarray:
    """Convert a PIL image into CV2 format."""
    image_cv: np.ndarray = np.array(image)

    return cv2.cvtColor(image_cv, cv2.COLOR_RGB2GRAY)
