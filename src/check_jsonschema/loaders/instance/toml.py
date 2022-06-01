from __future__ import annotations

import datetime
import typing as t

try:
    import tomli

    has_toml = True
except ImportError:
    has_toml = False

    load: t.Callable | None = None


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
        if isinstance(data, datetime.datetime):
            if data.tzinfo is None:
                return data.isoformat() + "Z"
            return data.isoformat()
        elif isinstance(data, datetime.time):
            if data.tzinfo is None:
                return data.isoformat() + "Z"
            return data.isoformat()
        elif isinstance(data, datetime.date):
            return data.isoformat()
        return data


if has_toml:

    def load(stream: t.TextIO) -> t.Any:
        data = tomli.load(stream)
        return _normalize(data)


# present a bool for detecting that it's enabled
ENABLED = load is not None


MISSING_SUPPORT_MESSAGE = """
check-jsonschema can only check TOML files when a TOML parser is installed

If you are running check-jsonschema as an installed python package, add support with
    pip install tomli

If you are running check-jsonschema as a pre-commit hook, set
    additional_dependencies: ['tomli']
"""
