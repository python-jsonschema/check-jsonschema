from __future__ import annotations

import typing as t

from .parsers import ParseError, ParserSet
from .transforms import Transform


class InstanceLoader:
    def __init__(
        self,
        files: t.Sequence[t.BinaryIO],
        default_filetype: str = "json",
        data_transform: Transform | None = None,
    ) -> None:
        self._files = files
        self._default_filetype = default_filetype
        self._data_transform = (
            data_transform if data_transform is not None else Transform()
        )

        self._parsers = ParserSet(
            modify_yaml_implementation=self._data_transform.modify_yaml_implementation
        )

    def iter_files(self) -> t.Iterator[tuple[str, ParseError | t.Any]]:
        for file in self._files:
            if not hasattr(file, "name"):
                raise ValueError(f"File {file} has no name attribute")
            try:
                data: t.Any = self._parsers.parse_data_with_path(
                    file, file.name, self._default_filetype
                )
            except ParseError as err:
                data = err
            else:
                data = self._data_transform(data)
            yield (file.name, data)
