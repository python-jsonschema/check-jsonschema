from __future__ import annotations

import pathlib
import re

from .utils import filename2path, is_url_ish

_YAML_SCHEMA_MODELINE_RE = re.compile(
    r"^[ \t]*#[ \t]*"
    r"(?:(?:yaml-language-server)[ \t]*:[ \t]*)?"
    r"\$schema[ \t]*(?:=|:)[ \t]*"
    r"(?P<schema>\S+)"
)


def extract_yaml_modeline_schema(data: bytes) -> str | None:
    text = data.decode("utf-8-sig", errors="replace")
    for line in text.splitlines():
        match = _YAML_SCHEMA_MODELINE_RE.match(line)
        if match:
            return match.group("schema")
    return None


def resolve_modeline_schema_location(schema_location: str, filename: str) -> str:
    if is_url_ish(schema_location) or pathlib.Path(schema_location).is_absolute():
        return schema_location

    if filename in ("-", "<stdin>"):
        raise ValueError(
            "relative schema paths in YAML modelines cannot be resolved for stdin"
        )

    return str(filename2path(filename).parent.joinpath(schema_location).resolve())
