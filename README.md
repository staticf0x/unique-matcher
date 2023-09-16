# PoE unique item matcher

A project aimed at detecting unique items on screen for PoE research purposes.

## Installation

For installation instructions, head to the wiki page [Installation](https://github.com/staticf0x/unique-matcher/wiki/Installation).

## Development

### Running tests

Run `tox -e pytest` to run unit tests. It *will* take a long time.

To run a single test, you can do for example:

```bash
pytest -v tests/test_matcher.py::test_get_base_name
```

To specify the testing data set to use, set `DATA_SET` environment variable
to the desired name. For example, to run the `example` data set:

```bash
DATA_SET=example pytest -v -n auto tests/test_matcher.py::test_find_item_contains_item
```

or use the helper script: `python3 run_tests.py` which lets you pick the data set interactively.

## Credits

### Research

nerdyjoe

### Test data, maps

Elinvynia, Krolya

### Testing
