import pytest

from unique_matcher.matcher.matcher import Matcher


@pytest.fixture(scope="session")
def matcher():
    return Matcher()
