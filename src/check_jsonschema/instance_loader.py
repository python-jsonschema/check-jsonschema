from __future__ import annotations

import io
from dataclasses import dataclass
import typing as t

from check_jsonschema.cli.param_types import CustomLazyFile

from .modeline import extract_yaml_modeline_schema, resolve_modeline_schema_location
from .parsers import ParseError, ParserSet
from .parsers.metadata import MultiDocumentData, ParsedDocument
from .transforms import Transform


@dataclass(frozen=True)
class InstanceDocument:
    filename: str
    data: t.Any
    line: int | None = None
    schemafile: str | None = None

    @property
    def label(self) -> str:
        if self.line is None:
            return self.filename
        return f"{self.filename}:{self.line}"


@dataclass(frozen=True)
class InstanceParseError:
    filename: str
    error: ParseError


@dataclass(frozen=True)
class LoadedFile:
    filename: str
    data: ParseError | t.Any
    schemafile: str | None = None


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

    def _apply_data_transform(self, data: t.Any) -> t.Any:
        if isinstance(data, MultiDocumentData):
            return MultiDocumentData(
                tuple(
                    ParsedDocument(
                        data=self._data_transform(document.data),
                        line=document.line,
                    )
                    for document in data.documents
                )
            )
        return self._data_transform(data)

    def _iter_loaded_files(self) -> t.Iterator[LoadedFile]:
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

            try:
                if isinstance(file, CustomLazyFile):
                    stream: t.IO[bytes] = t.cast(t.IO[bytes], file.open())
                else:
                    stream = file

                stream_bytes = stream.read()
                schemafile = None
                if self._schema_from_modeline:
                    raw_schemafile = extract_yaml_modeline_schema(stream_bytes)
                    if raw_schemafile is None:
                        continue
                    try:
                        schemafile = resolve_modeline_schema_location(
                            raw_schemafile, name
                        )
                    except ValueError as err:
                        data = ParseError(str(err))
                        yield LoadedFile(name, data, schemafile=None)
                        continue

                try:
                    data = self._parsers.parse_data_with_path(
                        stream_bytes, name, self._default_filetype, self._force_filetype
                    )
                except ParseError as err:
                    data = err
                else:
                    data = self._apply_data_transform(data)
            finally:
                file.close()
            yield LoadedFile(name, data, schemafile=schemafile)

    def iter_files(self) -> t.Iterator[tuple[str, ParseError | t.Any]]:
        for loaded_file in self._iter_loaded_files():
            yield (loaded_file.filename, loaded_file.data)

    def iter_documents(self) -> t.Iterator[InstanceDocument | InstanceParseError]:
        for loaded_file in self._iter_loaded_files():
            if isinstance(loaded_file.data, ParseError):
                yield InstanceParseError(loaded_file.filename, loaded_file.data)
            elif isinstance(loaded_file.data, MultiDocumentData):
                for document in loaded_file.data.documents:
                    yield InstanceDocument(
                        filename=loaded_file.filename,
                        data=document.data,
                        line=document.line,
                        schemafile=loaded_file.schemafile,
                    )
            else:
                yield InstanceDocument(
                    filename=loaded_file.filename,
                    data=loaded_file.data,
                    schemafile=loaded_file.schemafile,
                )
