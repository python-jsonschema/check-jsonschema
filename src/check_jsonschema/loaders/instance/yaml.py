import typing as t

import ruamel.yaml

_yaml = ruamel.yaml.YAML(typ="safe")

# ruamel.yaml parses timestamp values into datetime.datetime values which differs from
# JSON which parses timestamps as strings. Turn off this feature.
_yaml.constructor.yaml_constructors[
    "tag:yaml.org,2002:timestamp"
] = _yaml.constructor.yaml_constructors["tag:yaml.org,2002:str"]


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


def load(stream: t.BinaryIO) -> t.Any:
    data = _yaml.load(stream)
    return _normalize(data)
