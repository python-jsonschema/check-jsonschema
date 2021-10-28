import json
import pathlib
import typing as t
import urllib.parse

import jsonschema

from ..cachedownloader import CacheDownloader
from ..utils import is_url_ish
from .errors import SchemaParseError, UnsupportedUrlScheme


def json_load_schema(schema_location, fp):
    try:
        return json.load(fp)
    except ValueError:
        raise SchemaParseError(schema_location)


class LocalSchemaReader:
    def __init__(self, filename):
        self._filename = filename

    def read_schema(self):
        with open(self._filename) as f:
            return json_load_schema(self._filename, f)


class HttpSchemaReader:
    def __init__(self, url, cache_filename: t.Optional[str], disable_cache: bool):
        self._url = url
        self._downloader = CacheDownloader(
            url, cache_filename, disable_cache=disable_cache
        )

    def read_schema(self):
        with self._downloader.open() as fp:
            return json_load_schema(self._url, fp)


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


class SchemaLoader:
    def __init__(
        self,
        schemafile: str,
        cache_filename: t.Optional[str] = None,
        disable_cache: bool = False,
        format_enabled: bool = True,
    ):
        # record input parameters (these are not to be modified)
        self._schemafile = schemafile
        self._cache_filename = cache_filename
        self._disable_cache = disable_cache
        self._format_enabled = format_enabled

        # convert input path to be a resolved local file path or a URL, and then
        # parse that into parsed URL info
        url = self._schemafile
        if not is_url_ish(self._schemafile):
            path = pathlib.Path(self._schemafile)
            path = _resolve_path(path)
            url = path.as_uri()
        self._url_info = urllib.parse.urlparse(url)

        # setup a schema reader
        self._reader = self._get_schema_reader()

    def _get_schema_reader(self) -> t.Union[LocalSchemaReader, HttpSchemaReader]:
        if self._url_info.scheme in ("http", "https"):
            return HttpSchemaReader(
                self._schemafile, self._cache_filename, self._disable_cache
            )
        elif self._url_info.scheme in ("file", ""):
            return LocalSchemaReader(self._url_info.path)
        else:
            raise UnsupportedUrlScheme(
                "check-jsonschema only supports http, https, and local files. "
                f"detected parsed URL had an unrecognized scheme: {self._url_info}"
            )

    def get_validator(self):
        schema = self._reader.read_schema()
        format_checker = jsonschema.FormatChecker() if self._format_enabled else None
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema, format_checker=format_checker)
        return validator
