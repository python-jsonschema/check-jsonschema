import random

import pytest

from check_jsonschema.formats.implementations.rfc3339 import validate


@pytest.mark.parametrize(
    "datestr",
    (
        "2018-12-31T23:59:59Z",
        "2018-12-31t23:59:59Z",
        "2018-12-31t23:59:59z",
        "2018-12-31T23:59:59+00:00",
        "2018-12-31T23:59:59-00:00",
    ),
)
def test_simple_positive_cases(datestr):
    assert validate(datestr)


@pytest.mark.parametrize(
    "datestr",
    (
        object(),
        "2018-12-31T23:59:59",
        "2018-12-31T23:59:59+00:00Z",
        "2018-12-31 23:59:59",
    ),
)
def test_simple_negative_case(datestr):
    assert not validate(datestr)


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
    assert validate(f"2018-12-31T23:59:59.{fracsec}{offsetstr}")


@pytest.mark.parametrize(
    "datestr",
    (
        # no such month
        "2020-13-01T00:00:00Z",
        "2020-00-01T00:00:00Z",
        # no such day
        "2020-01-00T00:00:00Z",
        "2020-01-32T00:00:00Z",
    ),
)
def test_basic_bounds_validated(datestr):
    assert not validate(datestr)


@pytest.mark.parametrize(
    "month, maxday",
    (
        (1, 31),
        (3, 31),
        (4, 30),
        (5, 31),
        (6, 30),
        (7, 31),
        (8, 31),
        (9, 30),
        (10, 31),
        (11, 30),
    ),
)
def test_day_bounds_by_month(month, maxday):
    good_date = f"2020-{month:02}-{maxday:02}T00:00:00Z"
    bad_date = f"2020-{month:02}-{(maxday + 1):02}T00:00:00Z"
    assert validate(good_date)
    assert not validate(bad_date)


@pytest.mark.parametrize(
    "year, maxday",
    (
        (2018, 28),
        (2016, 29),
        (2400, 29),
        (2500, 28),
    ),
)
def test_day_bounds_for_february(year, maxday):
    good_date = f"{year}-02-{maxday:02}T00:00:00Z"
    bad_date = f"{year}-02-{(maxday + 1):02}T00:00:00Z"
    assert validate(good_date)
    assert not validate(bad_date)
