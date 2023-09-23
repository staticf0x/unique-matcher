"""Various utility functions."""

import csv
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def normalize_item_name(name: str) -> str:
    """Convert item name to file."""
    return name.replace("'", "").replace(" ", "_").replace(",", "")


def image_to_cv(image: Image.Image) -> np.ndarray:
    """Convert a PIL image into CV2 format."""
    image_cv: np.ndarray = np.array(image)

    return cv2.cvtColor(image_cv, cv2.COLOR_RGB2GRAY)


def calc_normalized_histogram(image: Image.Image) -> np.ndarray:
    """Calculate normalized histogram for an image.

    Algorithm taken from https://docs.opencv.org/3.4/d8/dc8/tutorial_histogram_comparison.html.
    """
    # Convert to CV2 format
    arr = np.array(image)

    # Change RGB to HSV (we're loading all PIL images as RGB)
    arr = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)

    # Calculate histogram
    hist = cv2.calcHist([arr], [0, 1], None, [50, 60], [0, 180, 0, 256], accumulate=False)

    # Normalize histogram
    return cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)


def is_csv_empty(file: Path) -> bool:
    """Return True if the provided CSV is empty."""
    with open(file, newline="") as fread:
        reader = csv.DictReader(fread)

        return len(list(reader)) == 0
