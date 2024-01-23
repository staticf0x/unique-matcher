"""These tests ensure a valid config before releasing, i.e. no debug stuff."""

import warnings

from unique_matcher import constants


def test_constants():
    assert constants.OPT_ALLOW_NON_FULLHD
    assert constants.OPT_FIND_ITEM_BY_NAME
    assert constants.OPT_IGNORE_NON_GLOBAL_ITEMS
    assert not constants.OPT_FIND_BY_NAME_RAISE
    assert constants.OPT_USE_MASK

    if constants.DEBUG:
        warnings.warn("DEBUG is True, should it be?", stacklevel=1)
