from __future__ import annotations

import json
import pathlib
import typing as t

import ruamel.yaml
from identify import identify

from . import json5, toml, yaml

DEFAULT_LOAD_FUNC_BY_TAG: dict[str, t.Callable[[t.BinaryIO], t.Any]] = {
    "json": json.load,
}
if json5.ENABLED:
    DEFAULT_LOAD_FUNC_BY_TAG["json5"] = json5.load
if toml.ENABLED:
    DEFAULT_LOAD_FUNC_BY_TAG["toml"] = toml.load
MISSING_SUPPORT_MESSAGES: dict[str, str] = {
    "json5": json5.MISSING_SUPPORT_MESSAGE,
    "toml": toml.MISSING_SUPPORT_MESSAGE,
}


class BadFileTypeError(ValueError):
    pass


class ParserSet:
    def __init__(
        self,
        *,
        modify_yaml_implementation: t.Callable[[ruamel.yaml.YAML], ruamel.yaml.YAML]
        | None = None,
        supported_formats: t.Sequence[str, ...] | None = None,
    ) -> None:
        yaml_impl = yaml.construct_yaml_implementation()
        if modify_yaml_implementation:
            modify_yaml_implementation(yaml_impl)
        base_by_tag = {
            "yaml": yaml.impl2loader(yaml_impl),
            **DEFAULT_LOAD_FUNC_BY_TAG,
        }
        if supported_formats is None:
            self._by_tag = base_by_tag
        else:
            self._by_tag = {
                k: v for k, v in base_by_tag.items() if k in supported_formats
            }

    def get(
        self, filename: str, default_ft: str | None
    ) -> t.Callable[[t.BinaryIO], t.Any]:
        tags = identify.tags_from_path(filename)
        for (tag, loadfunc) in self._by_tag.items():
            if tag in tags:
                return loadfunc
        if default_ft in self._by_tag:
            return self._by_tag[default_ft]

        for tag in tags:
            if tag in MISSING_SUPPORT_MESSAGES:
                raise BadFileTypeError(
                    f"cannot parse {filename} because support is missing for {tag}\n"
                    + MISSING_SUPPORT_MESSAGES[tag]
                )
        raise BadFileTypeError(
            f"cannot parse {filename} as it is not one of the supported filetypes: "
            + ",".join(self._by_tag.keys())
        )

    def parse_file(
        self,
        path: str | pathlib.Path,
        default_ft: str | None,
    ):
        loadfunc = self.get(
            str(path) if isinstance(path, pathlib.Path) else path, default_ft
        )
        with open(path, "rb") as fp:
            return loadfunc(fp)
