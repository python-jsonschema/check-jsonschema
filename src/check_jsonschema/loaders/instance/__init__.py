from __future__ import annotations

import json
import typing as t

from identify import identify

from ...transforms import Transform
from ..errors import BadFileTypeError
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


class ParserSet:
    def __init__(self, transform: Transform):
        yaml_impl = yaml.construct_yaml_implementation()
        transform.modify_yaml_implementation(yaml_impl)
        self._by_tag = {
            "yaml": yaml.impl2loader(yaml_impl),
            **DEFAULT_LOAD_FUNC_BY_TAG,
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
                    f"cannot check {filename} because support is missing for {tag}\n"
                    + MISSING_SUPPORT_MESSAGES[tag]
                )
        raise BadFileTypeError(
            f"cannot check {filename} as it is not one of the supported filetypes: "
            + ",".join(self._by_tag.keys())
        )


class InstanceLoader:
    def __init__(
        self,
        filenames: t.Sequence[str],
        default_filetype: str | None = None,
        data_transform: Transform | None = None,
    ) -> None:
        self._filenames = filenames
        self._default_ft = default_filetype.lower() if default_filetype else None
        self._data_transform = (
            data_transform if data_transform is not None else Transform()
        )

        self._parsers = ParserSet(self._data_transform)

    def iter_files(self) -> t.Iterator[tuple[str, t.Any]]:
        for fn in self._filenames:
            loadfunc = self._parsers.get(fn, self._default_ft)

            with open(fn, "rb") as fp:
                data = loadfunc(fp)
                data = self._data_transform(data)
                yield (fn, data)
