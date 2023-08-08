from __future__ import annotations

import io
import typing as t

import ruamel.yaml

from ..cachedownloader import CacheDownloader
from ..parsers import ParserSet
from ..utils import filename2path
from .errors import SchemaParseError

yaml = ruamel.yaml.YAML(typ="safe")


def _run_load_callback(schema_location: str, callback: t.Callable) -> dict:
    try:
        schema = callback()
    # only local loads can raise the YAMLError, but catch for both cases for simplicity
    except (ValueError, ruamel.yaml.error.YAMLError) as e:
        raise SchemaParseError(schema_location) from e
    if not isinstance(schema, dict):
        raise SchemaParseError(schema_location)
    return schema


class LocalSchemaReader:
    def __init__(self, filename: str) -> None:
        self.path = filename2path(filename)
        self.filename = str(self.path)
        self.parsers = ParserSet()

    def get_retrieval_uri(self) -> str:
        return self.path.as_uri()

    def _read_impl(self) -> t.Any:
        return self.parsers.parse_file(self.path, default_filetype="json")

    def read_schema(self) -> dict:
        return _run_load_callback(self.filename, self._read_impl)


class HttpSchemaReader:
    def __init__(
        self,
        url: str,
        cache_filename: str | None,
        disable_cache: bool,
    ) -> None:
        self.url = url
        self.parsers = ParserSet()
        self.downloader = CacheDownloader(
            url,
            cache_filename,
            disable_cache=disable_cache,
            validation_callback=self._parse,
        )
        self._parsed_schema: t.Any | None = None

    def _parse(self, schema_bytes: bytes) -> t.Any:
        if self._parsed_schema is None:
            self._parsed_schema = self.parsers.parse_data_with_path(
                io.BytesIO(schema_bytes), self.url, default_filetype="json"
            )
        return self._parsed_schema

    def get_retrieval_uri(self) -> str:
        return self.url

    def _read_impl(self) -> t.Any:
        with self.downloader.open() as fp:
            return self._parse(fp.read())

    def read_schema(self) -> dict:
        return _run_load_callback(self.url, self._read_impl)
