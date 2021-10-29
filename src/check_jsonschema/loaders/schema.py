import json
import pathlib
import typing as t
import urllib.parse

import jsonschema

from ..cachedownloader import CacheDownloader
from ..utils import is_url_ish
from .errors import SchemaParseError, UnsupportedUrlScheme


def _json_load_schema(schema_location, fp):
    try:
        return json.load(fp)
    except ValueError:
        raise SchemaParseError(schema_location)


def _resolve_path(path):
    """
    This is a testing shim which wraps
        pathlib.Path.expanduser
    and
        pathlib.Path.resolve

    for path resolution.

    The purpose of this method is to be mock-friendly.
    """
    return path.expanduser().resolve()


class LocalSchemaReader:
    def __init__(self, filename):
        self.filename = filename
        path = pathlib.Path(filename)
        self.resolved_filename = str(_resolve_path(path))

    def read_schema(self):
        with open(self.resolved_filename) as f:
            return _json_load_schema(self.filename, f)


class HttpSchemaReader:
    def __init__(self, url, cache_filename: t.Optional[str], disable_cache: bool):
        self.url = url
        self.downloader = CacheDownloader(
            url, cache_filename, disable_cache=disable_cache
        )

    def read_schema(self):
        with self.downloader.open() as fp:
            return _json_load_schema(self.url, fp)


class SchemaLoader:
    def __init__(
        self,
        schemafile: str,
        cache_filename: t.Optional[str] = None,
        disable_cache: bool = False,
        format_enabled: bool = True,
    ):
        # record input parameters (these are not to be modified)
        self.schemafile = schemafile
        self.cache_filename = cache_filename
        self.disable_cache = disable_cache
        self.format_enabled = format_enabled

        # if the schema location is a URL, which may include a file:// URL, parse it
        self.url_info = None
        if is_url_ish(self.schemafile):
            self.url_info = urllib.parse.urlparse(self.schemafile)

        # setup a schema reader
        self.reader = self.get_schema_reader()

    def get_schema_reader(self) -> t.Union[LocalSchemaReader, HttpSchemaReader]:
        if self.url_info is None:
            return LocalSchemaReader(self.schemafile)

        if self.url_info.scheme in ("http", "https"):
            return HttpSchemaReader(
                self.schemafile, self.cache_filename, self.disable_cache
            )
        elif self.url_info.scheme in ("file", ""):
            return LocalSchemaReader(self.url_info.path)
        else:
            raise UnsupportedUrlScheme(
                "check-jsonschema only supports http, https, and local files. "
                f"detected parsed URL had an unrecognized scheme: {self.url_info}"
            )

    def get_validator(self):
        schema = self.reader.read_schema()
        format_checker = jsonschema.FormatChecker() if self.format_enabled else None
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema, format_checker=format_checker)
        return validator
