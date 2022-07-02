from __future__ import annotations

import typing as t

import ruamel.yaml

from ...transforms import Transform


def _construct_yaml_implementation() -> ruamel.yaml.YAML:
    implementation = ruamel.yaml.YAML(typ="safe")

    # ruamel.yaml parses timestamp values into datetime.datetime values
    # however, JSON does not support native datetimes, so JSON Schema formats for
    # dates apply to strings
    # Turn off this feature, instructing the parser to load datetimes as strings
    implementation.constructor.yaml_constructors[
        "tag:yaml.org,2002:timestamp"
    ] = implementation.constructor.yaml_constructors["tag:yaml.org,2002:str"]

    return implementation


def _normalize(data: t.Any) -> t.Any:
    """
    Normalize YAML data to fit the requirements to be JSON-encodeable.

    Currently this applies the following transformation:
        dict keys are converted to strings

    Additional tweaks can be added in this layer in the future if necessary.
    """
    if isinstance(data, dict):
        return {str(k): _normalize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_normalize(x) for x in data]
    else:
        return data


_YAML_IMPLEMENTATION_CACHE: dict[Transform, ruamel.yaml.YAML] = {}


def load(stream: t.BinaryIO, *, data_transform: Transform) -> t.Any:
    if data_transform in _YAML_IMPLEMENTATION_CACHE:
        implementation = _YAML_IMPLEMENTATION_CACHE[data_transform]
    else:
        implementation = _construct_yaml_implementation()
        data_transform.modify_yaml_implementation(implementation)
        _YAML_IMPLEMENTATION_CACHE[data_transform] = implementation

    data = implementation.load(stream)
    data = _normalize(data)
    return data_transform(data)
