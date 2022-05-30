from __future__ import annotations

import json
import typing as t

from identify import identify

from ...transforms import TransformT
from ..errors import BadFileTypeError
from . import json5, toml, yaml

LOAD_FUNC_BY_TAG: dict[str, t.Callable] = {
    "json": json.load,
    "yaml": yaml.load,
}
if json5.ENABLED:
    LOAD_FUNC_BY_TAG["json5"] = json5.load  # type: ignore[assignment]
if toml.ENABLED:
    LOAD_FUNC_BY_TAG["toml"] = toml.load  # type: ignore[assignment]
MISSING_SUPPORT_MESSAGES: dict[str, str] = {
    "json5": json5.MISSING_SUPPORT_MESSAGE,
    "toml": toml.MISSING_SUPPORT_MESSAGE,
}


class InstanceLoader:
    def __init__(
        self,
        filenames: t.Sequence[str],
        default_filetype: str | None = None,
        data_transform: TransformT | None = None,
    ) -> None:
        self._filenames = filenames
        self._default_ft = default_filetype.lower() if default_filetype else None
        self._data_transform = data_transform

    def get_loadfunc(self, filename: str) -> t.Callable:
        tags = identify.tags_from_path(filename)
        for (tag, loadfunc) in LOAD_FUNC_BY_TAG.items():
            if tag in tags:
                return loadfunc
        if self._default_ft in LOAD_FUNC_BY_TAG:
            return LOAD_FUNC_BY_TAG[self._default_ft]

        for tag in tags:
            if tag in MISSING_SUPPORT_MESSAGES:
                raise BadFileTypeError(
                    f"cannot check {filename} because support is missing for {tag}\n"
                    + MISSING_SUPPORT_MESSAGES[tag]
                )
        raise BadFileTypeError(
            f"cannot check {filename} as it is not one of the supported filetypes: "
            + ",".join(LOAD_FUNC_BY_TAG.keys())
        )

    def iter_files(self) -> t.Iterator[tuple[str, t.Any]]:
        for fn in self._filenames:
            loadfunc = self.get_loadfunc(fn)

            with open(fn, "rb") as fp:
                data = loadfunc(fp)
                if self._data_transform:
                    data = self._data_transform(data)
                yield (fn, data)
