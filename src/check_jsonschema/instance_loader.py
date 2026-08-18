from __future__ import annotations

import io
import typing as t

from check_jsonschema.cli.param_types import CustomLazyFile

from .modeline import extract_yaml_modeline_schema, resolve_modeline_schema_location
from .parsers import ParseError, ParserSet
from .transforms import Transform

LoadedFile = tuple[str, ParseError | t.Any, str | None]


class InstanceLoader:
    def __init__(
        self,
        files: t.Sequence[t.IO[bytes] | CustomLazyFile],
        default_filetype: str = "json",
        force_filetype: str | None = None,
        data_transform: Transform | None = None,
        schema_from_modeline: bool = False,
    ) -> None:
        self._files = files
        self._default_filetype = default_filetype
        self._force_filetype = force_filetype
        self._schema_from_modeline = schema_from_modeline
        self._data_transform = (
            data_transform if data_transform is not None else Transform()
        )

        self._parsers = ParserSet(
            modify_yaml_implementation=self._data_transform.modify_yaml_implementation
        )

    def iter_files(self) -> t.Iterator[LoadedFile]:
        for file in self._files:
            if hasattr(file, "name"):
                name = file.name
            # allowing for BytesIO to be special-cased here is useful for
            # simpler test setup, since this is what tests will pass and we naturally
            # support it here
            elif isinstance(file, io.BytesIO) or file.fileno() == 0:
                name = "<stdin>"
            else:
                raise ValueError(f"File {file} has no name attribute")

            data: ParseError | t.Any
            schema_file: str | None = None
            try:
                if isinstance(file, CustomLazyFile):
                    stream: t.IO[bytes] = t.cast(t.IO[bytes], file.open())
                else:
                    stream = file

                data_stream = stream.read()
                try:
                    if self._schema_from_modeline:
                        schema_file = self._resolve_schema_from_modeline(
                            data_stream, name
                        )
                        # Skip files that don't have a modeline schema
                        if not schema_file:
                            continue
                    data = self._parsers.parse_data_with_path(
                        data_stream,
                        name,
                        self._default_filetype,
                        self._force_filetype,
                    )
                except ParseError as err:
                    data = err
                else:
                    data = self._data_transform(data)
            finally:
                file.close()
            yield name, data, schema_file

    @staticmethod
    def _resolve_schema_from_modeline(data: bytes, name: str) -> str | None:
        raw_schemafile = extract_yaml_modeline_schema(data)
        if raw_schemafile is None:
            return None
        try:
            schemafile = resolve_modeline_schema_location(raw_schemafile, name)
            return schemafile
        except ValueError as err:
            raise ParseError(str(err))
