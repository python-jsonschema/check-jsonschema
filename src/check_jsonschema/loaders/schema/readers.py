import json
import pathlib
import typing as t

import identify
import ruamel.yaml

from ...cachedownloader import CacheDownloader
from ..errors import SchemaParseError

yaml = ruamel.yaml.YAML(typ="safe")


def _json_load_schema(schema_location: str, fp) -> dict:
    try:
        schema = json.load(fp)
    except ValueError:
        raise SchemaParseError(schema_location)
    if not isinstance(schema, dict):
        raise SchemaParseError(schema_location)
    return schema


def _yaml_load_schema(schema_location: str, fp) -> dict:
    try:
        schema = yaml.load(fp)
    except ruamel.yaml.error.YAMLError:
        raise SchemaParseError(schema_location)
    if not isinstance(schema, dict):
        raise SchemaParseError(schema_location)
    return schema


class LocalSchemaReader:
    def __init__(self, filename):
        self.filename = filename
        self.path = pathlib.Path(filename).expanduser().resolve()

    def get_ref_base(self) -> str:
        return self.path.as_uri()

    def read_schema(self):
        tags = identify.identify.tags_from_path(self.filename)
        with self.path.open() as f:
            if "yaml" in tags:
                return _yaml_load_schema(self.filename, f)
            elif "json" in tags:
                return _json_load_schema(self.filename, f)
            else:
                return _json_load_schema(self.filename, f)


class HttpSchemaReader:
    def __init__(
        self,
        url,
        cache_filename: t.Optional[str],
        disable_cache: bool,
    ):
        self.url = url
        self.downloader = CacheDownloader(
            url, cache_filename, disable_cache=disable_cache
        )

    def get_ref_base(self) -> str:
        return self.url

    def read_schema(self):
        with self.downloader.open() as fp:
            return _json_load_schema(self.url, fp)
