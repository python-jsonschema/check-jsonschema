import random

import pytest

from check_jsonschema.formats.implementations.iso8601_time import validate


@pytest.mark.parametrize(
    "timestr",
    (
        "12:34:56Z",
        "23:59:59z",
        "23:59:59+00:00",
        "01:59:59-00:00",
    ),
)
def test_simple_positive_cases(timestr):
    assert validate(timestr)


@pytest.mark.parametrize(
    "timestr",
    (
        object(),
        "12:34:56",
        "23:59:60Z",
        "23:59:59+24:00",
        "01:59:59-00:60",
        "01:01:00:00:60",
    ),
)
def test_simple_negative_cases(timestr):
    assert not validate(timestr)


@pytest.mark.parametrize("precision", list(range(20)))
@pytest.mark.parametrize(
    "offsetstr",
    (
        "Z",
        "+00:00",
        "-00:00",
        "+23:59",
    ),
)
def test_allows_fracsec(precision, offsetstr):
    fracsec = random.randint(0, 10**precision)
    assert validate(f"23:59:59.{fracsec}{offsetstr}")
