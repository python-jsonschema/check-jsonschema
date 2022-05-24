from __future__ import annotations

try:
    # first, try to import the installed package version
    import importlib_resources
except ImportError:
    # if it's not installed, assume that the stdlib version is new enough (e.g. py3.10)
    import importlib.resources as importlib_resources  # type: ignore[no-redef]

import json
import typing as t


class NoSuchSchemaError(ValueError):
    pass


def _get(package: str, resource: str, name: str) -> dict[str, t.Any]:
    try:
        return t.cast(
            "dict[str, t.Any]",
            json.loads(
                importlib_resources.files(package).joinpath(resource).read_bytes()
            ),
        )
    except (FileNotFoundError, ModuleNotFoundError):
        raise NoSuchSchemaError(f"no builtin schema named {name} was found")


def _get_vendored_schema(name: str) -> dict[str, t.Any]:
    return _get("check_jsonschema.builtin_schemas.vendor", f"{name}.json", name)


def _get_custom_schema(name: str) -> dict[str, t.Any]:
    return _get("check_jsonschema.builtin_schemas.custom", f"{name}.json", name)


def get_builtin_schema(name: str) -> dict[str, t.Any]:
    # first, look for an identifying prefix
    if name.startswith("vendor."):
        return _get_vendored_schema(name[7:])
    elif name.startswith("custom."):
        return _get_custom_schema(name[7:])

    # if there is no prefix, just try in order: first custom, then vendored
    try:
        return _get_custom_schema(name)
    except NoSuchSchemaError:
        return _get_vendored_schema(name)
