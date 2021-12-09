try:
    import importlib.resources as importlib_resources
except ImportError:
    import importlib_resources

import json
import typing as t


class NoSuchSchemaError(ValueError):
    pass


def _get(package: str, resource: str, name: str) -> t.Dict[str, t.Any]:
    try:
        return json.loads(importlib_resources.read_text(package, resource))
    except (FileNotFoundError, ModuleNotFoundError):
        raise NoSuchSchemaError(f"no builtin schema named {name} was found")


def get_vendored_schema(name: str) -> t.Dict[str, t.Any]:
    return _get("check_jsonschema.builtin_schemas.vendor", f"{name}.json", name)


def get_custom_schema(name: str) -> t.Dict[str, t.Any]:
    return _get("check_jsonschema.builtin_schemas.custom", f"{name}.json", name)


def get_builtin_schema_from_external_name(name: str) -> t.Optional[t.Dict[str, t.Any]]:
    if name.startswith("vendor."):
        return get_vendored_schema(name[7:])
    elif name.startswith("custom."):
        return get_custom_schema(name[7:])
    return get_custom_schema(name)
