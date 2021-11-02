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


class LocalSchemaReader:
    def __init__(self, filename):
        self.filename = filename
        self.path = pathlib.Path(filename)
        self.abs_path = self.path.expanduser().resolve()

    def get_ref_base(self) -> str:
        return self.abs_path.as_uri()

    def read_schema(self):
        with self.abs_path.open() as f:
            return _json_load_schema(self.filename, f)


class HttpSchemaReader:
    def __init__(self, url, cache_filename: t.Optional[str], disable_cache: bool):
        self.url = url
        self.downloader = CacheDownloader(
            url, cache_filename, disable_cache=disable_cache
        )

    def get_ref_base(self) -> str:
        return self.url

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

        # format checker (which may be None)
        format_checker = jsonschema.FormatChecker() if self.format_enabled else None

        # ref resolver which is built from the schema path
        # if the location is a URL, there's no change, but if it's a file path
        # it's made absolute and URI-ized
        ref_resolver = jsonschema.RefResolver(self.reader.get_ref_base(), schema)

        # get the correct validator class and check the schema under its metaschema
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)

        # now that we know it's safe to try to create the validator instance, do it
        validator = validator_cls(
            schema,
            resolver=ref_resolver,
            format_checker=format_checker,
        )
        return validator
