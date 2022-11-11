"""
Identify filetypes by extension
"""
from __future__ import annotations

import pathlib

_EXTENSION_MAP = {
    "json": "json",
    "jsonld": "json",
    "geojson": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "ymlld": "yaml",
    "eyaml": "yaml",
    "json5": "json5",
    "toml": "toml",
}


def path_to_type(path: pathlib.Path, *, default_type: str = "json") -> str:
    ext = path.suffix.lstrip(".")

    if ext in _EXTENSION_MAP:
        return _EXTENSION_MAP[ext]

    return default_type
