from __future__ import annotations

import datetime
import typing as t

try:
    import tomli

    has_toml = True
except ImportError:
    has_toml = False


def _normalize(data: t.Any) -> t.Any:
    """
    Normalize TOML data to fit the requirements to be JSON-encodeable.

    Currently this applies the following transformations:

        offset-aware datetime.datetime values are converted to strings using isoformat()
        naive datetime.datetime values are converted to strings using isoformat() + "Z"

        offset-aware datetime.time values are converted to strings using isoformat()
        naive datetime.time values are converted to strings using isoformat() + "Z"

        datetime.date values are converted to strings using isoformat()
    """
    if isinstance(data, dict):
        return {k: _normalize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_normalize(x) for x in data]
    else:
        # python's datetime will format to an ISO partial time when handling a naive
        # time/datetime , but JSON Schema format validation specifies that date-time is
        # taken from RFC3339, which defines "date-time" as including 'Z|offset'
        # the specification for "time" is less clear because JSON Schema does not specify
        # which RFC3339 definition should be used, and the RFC has no format named "time",
        # only "full-time" (with Z|offset) and "partial-time" (no offset)
        #
        # rfc3339_validator (used by 'jsonschema') requires the offset, so we will do the
        # same
        if isinstance(data, datetime.datetime) or isinstance(data, datetime.time):
            if data.tzinfo is None:
                return data.isoformat() + "Z"
            return data.isoformat()
        elif isinstance(data, datetime.date):
            return data.isoformat()
        return data


# present a bool for detecting that it's enabled
ENABLED = has_toml


if has_toml:
    ParseError: type[Exception] = tomli.TOMLDecodeError

    def load(stream: t.BinaryIO) -> t.Any:
        data = tomli.load(stream)
        return _normalize(data)

else:
    ParseError = ValueError

    def load(stream: t.BinaryIO) -> t.Any:
        raise NotImplementedError


MISSING_SUPPORT_MESSAGE = """
check-jsonschema can only parse TOML files when a TOML parser is installed

If you are running check-jsonschema as an installed python package, add support with
    pip install tomli

If you are running check-jsonschema as a pre-commit hook, set
    additional_dependencies: ['tomli']
"""
