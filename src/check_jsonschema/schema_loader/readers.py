from __future__ import annotations

import json
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
    FORMATS = ("json", "json5", "yaml")

    def __init__(self, filename: str) -> None:
        self.path = filename2path(filename)
        self.filename = str(self.path)
        self.parsers = ParserSet(supported_formats=self.FORMATS)

    def get_ref_base(self) -> str:
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
        self.downloader = CacheDownloader(
            url,
            cache_filename,
            disable_cache=disable_cache,
            validation_callback=json.loads,
        )

    def get_ref_base(self) -> str:
        return self.url

    def _read_impl(self) -> t.Any:
        with self.downloader.open() as fp:
            return json.load(fp)

    def read_schema(self) -> dict:
        return _run_load_callback(self.url, self._read_impl)
