# PoE unique item matcher

A project aimed at detecting unique items on screen for PoE research purposes.

## Installation

You need Python 3.11+ and [Poetry](https://github.com/python-poetry/poetry).

1. Install poetry: `pip3 install --user poetry`
2. Install project dependencies: `poetry install`
3. Enter Poetry shell: `poetry shell`

### Tesseract

This program requires `tesseract` to be available at your system.
Refer to the [official installation guide](https://tesseract-ocr.github.io/tessdoc/Installation.html) to install it.

## Development

### Running tests

Run `tox -e pytest` to run unit tests. It *will* take a long time.
