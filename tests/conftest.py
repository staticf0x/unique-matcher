import pytest

from unique_matcher.matcher.matcher import Matcher


@pytest.fixture(scope="session")
def matcher():
    return Matcher()


@pytest.fixture(scope="session")
def item_loader(matcher):
    return matcher.item_loader
