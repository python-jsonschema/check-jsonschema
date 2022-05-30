from __future__ import annotations

import typing as t

try:
    import tomli

    load: t.Callable | None = tomli.load
except ImportError:
    load = None

# present a bool for detecting that it's enabled
ENABLED = load is not None

MISSING_SUPPORT_MESSAGE = """
check-jsonschema can only check TOML files when a TOML parser is installed

If you are running check-jsonschema as an installed python package, add support with
    pip install tomli

If you are running check-jsonschema as a pre-commit hook, set
    additional_dependencies: ['tomli']
"""
