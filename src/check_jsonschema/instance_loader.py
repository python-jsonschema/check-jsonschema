from __future__ import annotations

import pathlib
import typing as t

from .parsers import ParseError, ParserSet
from .transforms import Transform


class InstanceLoader:
    def __init__(
        self,
        filenames: t.Sequence[str],
        default_filetype: str = "json",
        data_transform: Transform | None = None,
    ) -> None:
        self._filenames = filenames
        self._default_filetype = default_filetype
        self._data_transform = (
            data_transform if data_transform is not None else Transform()
        )

        self._parsers = ParserSet(
            modify_yaml_implementation=self._data_transform.modify_yaml_implementation
        )

    def iter_files(self) -> t.Iterator[tuple[pathlib.Path, ParseError | t.Any]]:
        for fn in self._filenames:
            path = pathlib.Path(fn)
            try:
                data: t.Any = self._parsers.parse_file(path, self._default_filetype)
            except ParseError as err:
                data = err
            else:
                data = self._data_transform(data)
            yield (path, data)
