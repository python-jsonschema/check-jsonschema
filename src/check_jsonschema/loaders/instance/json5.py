from __future__ import annotations

import typing as t

from ...transforms import Transform

# try to import pyjson5 first
# this is the CPython implementation and therefore preferred for its speec
try:
    import pyjson5

    _load: t.Callable | None = pyjson5.load
except ImportError:
    # if pyjson5 was not available, try to import 'json5', the pure-python implementation
    try:
        import json5

        _load = json5.load
    except ImportError:
        _load = None

# present a bool for detecting that it's enabled
ENABLED = _load is not None

if _load is not None:
    _load_concrete: t.Callable = _load

    def load(stream: t.BinaryIO, *, data_transform: Transform) -> t.Any:
        data = _load_concrete(stream)
        return data_transform(data)

else:

    def load(stream: t.BinaryIO, *, data_transform: Transform) -> t.Any:
        raise NotImplementedError


MISSING_SUPPORT_MESSAGE = """
check-jsonschema can only check json5 files when a json5 parser is installed

If you are running check-jsonschema as an installed python package, either
    pip install json5
or
    pip install pyjson5

If you are running check-jsonschema as a pre-commit hook, set
    additional_dependencies: ['json5']
or
    additional_dependencies: ['pyjson5']
"""
