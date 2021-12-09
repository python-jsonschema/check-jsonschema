import json
import pathlib
import typing as t
import urllib.error
import urllib.parse

import jsonschema

from ..builtin_schemas import get_builtin_schema
from ..cachedownloader import CacheDownloader
from ..utils import is_url_ish
from .errors import SchemaParseError, UnsupportedUrlScheme


def _make_ref_resolver(
    schema_uri: t.Optional[str], schema: dict
) -> t.Optional[jsonschema.RefResolver]:
    if not schema_uri:
        return None

    base_uri = schema.get("$id", schema_uri)
    return jsonschema.RefResolver(base_uri, schema)


def _json_load_schema(schema_location: str, fp) -> dict:
    try:
        schema = json.load(fp)
    except ValueError:
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
        with self.path.open() as f:
            return _json_load_schema(self.filename, f)


class HttpSchemaReader:
    def __init__(
        self,
        url,
        cache_filename: t.Optional[str],
        disable_cache: bool,
        failover_builtin_schema: t.Optional[str] = None,
    ):
        self.url = url
        self.failover_builtin_schema = failover_builtin_schema
        self.downloader = CacheDownloader(
            url, cache_filename, disable_cache=disable_cache
        )

    def get_ref_base(self) -> str:
        return self.url

    def read_schema(self):
        try:
            with self.downloader.open() as fp:
                return _json_load_schema(self.url, fp)
        except urllib.error.URLError as err:
            if self.failover_builtin_schema:
                val = get_builtin_schema(self.failover_builtin_schema)
                if val:
                    return val
                else:
                    raise ValueError(
                        f"failover schema {self.failover_builtin_schema} not valid"
                    ) from err
            raise


class SchemaLoader:
    def __init__(
        self,
        schemafile: str,
        cache_filename: t.Optional[str] = None,
        disable_cache: bool = False,
        failover_builtin_schema: t.Optional[str] = None,
    ):
        # record input parameters (these are not to be modified)
        self.schemafile = schemafile
        self.cache_filename = cache_filename
        self.disable_cache = disable_cache
        self.failover_builtin_schema = failover_builtin_schema

        # if the schema location is a URL, which may include a file:// URL, parse it
        self.url_info = None
        if is_url_ish(self.schemafile):
            self.url_info = urllib.parse.urlparse(self.schemafile)

        # setup a schema reader
        self.reader = self._get_schema_reader()

    def _get_schema_reader(self) -> t.Union[LocalSchemaReader, HttpSchemaReader]:
        if self.url_info is None:
            return LocalSchemaReader(self.schemafile)

        if self.url_info.scheme in ("http", "https"):
            return HttpSchemaReader(
                self.schemafile,
                self.cache_filename,
                self.disable_cache,
                self.failover_builtin_schema,
            )
        elif self.url_info.scheme in ("file", ""):
            return LocalSchemaReader(self.url_info.path)
        else:
            raise UnsupportedUrlScheme(
                "check-jsonschema only supports http, https, and local files. "
                f"detected parsed URL had an unrecognized scheme: {self.url_info}"
            )

    def get_schema_ref_base(self) -> t.Optional[str]:
        return self.reader.get_ref_base()

    def get_schema(self) -> t.Dict[str, t.Any]:
        return self.reader.read_schema()

    def make_validator(self, format_enabled: bool):
        schema_uri = self.get_schema_ref_base()
        schema = self.get_schema()

        # format checker (which may be None)
        format_checker = jsonschema.FormatChecker() if format_enabled else None

        # ref resolver which may be built from the schema path
        # if the location is a URL, there's no change, but if it's a file path
        # it's made absolute and URI-ized
        # the resolver should use `$id` if there is one present in the schema
        ref_resolver = _make_ref_resolver(schema_uri, schema)

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


class BuiltinSchemaLoader(SchemaLoader):
    def __init__(self, schema_name: str) -> None:
        self.schema_name = schema_name

    def get_schema_ref_base(self) -> t.Optional[str]:
        return None

    def get_schema(self) -> t.Dict[str, t.Any]:
        return get_builtin_schema(self.schema_name)


def schema_loader_from_args(args) -> SchemaLoader:
    if args.schemafile is not None:
        return SchemaLoader(
            args.schemafile,
            args.cache_filename,
            args.no_cache,
            args.failover_builtin_schema,
        )
    else:
        return BuiltinSchemaLoader(args.builtin_schema)
