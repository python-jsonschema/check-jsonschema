try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources

import json
import typing as t


def _get_or_none(package: str, resource: str) -> t.Optional[t.Dict[str, t.Any]]:
    try:
        return json.loads(importlib_resources.read_text(package, resource))
    except (FileNotFoundError, ModuleNotFoundError):
        return None


def get_vendored_schema(name: str) -> t.Optional[t.Dict[str, t.Any]]:
    return _get_or_none("check_jsonschema.builtin_schemas.vendor", f"{name}.json")


def get_custom_schema(name: str) -> t.Optional[t.Dict[str, t.Any]]:
    return _get_or_none("check_jsonschema.builtin_schemas.custom", f"{name}.json")


def get_builtin_schema_from_external_name(name: str) -> t.Optional[t.Dict[str, t.Any]]:
    if name.startswith("vendor."):
        return get_vendored_schema(name[7:])
    elif name.startswith("custom."):
        return get_custom_schema(name[7:])
    return get_custom_schema(name)
