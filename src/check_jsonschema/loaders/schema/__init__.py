import typing as t
import urllib.error
import urllib.parse

import jsonschema

from ...builtin_schemas import get_builtin_schema
from ...formats import FormatOptions, make_format_checker
from ...utils import is_url_ish
from ..errors import UnsupportedUrlScheme
from .readers import HttpSchemaReader, LocalSchemaReader


def _make_ref_resolver(
    schema_uri: t.Optional[str], schema: dict
) -> t.Optional[jsonschema.RefResolver]:
    if not schema_uri:
        return None

    base_uri = schema.get("$id", schema_uri)
    return jsonschema.RefResolver(base_uri, schema)


class SchemaLoaderBase:
    def get_validator(
        self,
        instance_filename: str,
        instance_doc: t.Dict[str, t.Any],
        format_opts: FormatOptions,
    ):
        raise NotImplementedError


class SchemaLoader(SchemaLoaderBase):
    def __init__(
        self,
        schemafile: str,
        cache_filename: t.Optional[str] = None,
        disable_cache: bool = False,
    ):
        # record input parameters (these are not to be modified)
        self.schemafile = schemafile
        self.cache_filename = cache_filename
        self.disable_cache = disable_cache

        # if the schema location is a URL, which may include a file:// URL, parse it
        self.url_info = None
        if is_url_ish(self.schemafile):
            self.url_info = urllib.parse.urlparse(self.schemafile)

        # setup a schema reader lazily, when needed
        self._reader = None

        # setup a location to store the validator so that it is only built once by default
        self._validator = None

    @property
    def reader(self) -> t.Union[LocalSchemaReader, HttpSchemaReader]:
        if self._reader is None:
            self._reader = self._get_schema_reader()
        return self._reader

    def _get_schema_reader(self) -> t.Union[LocalSchemaReader, HttpSchemaReader]:
        if self.url_info is None:
            return LocalSchemaReader(self.schemafile)

        if self.url_info.scheme in ("http", "https"):
            return HttpSchemaReader(
                self.schemafile,
                self.cache_filename,
                self.disable_cache,
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

    def make_validator(self, format_opts: FormatOptions):
        schema_uri = self.get_schema_ref_base()
        schema = self.get_schema()

        # format checker (which may be None)
        format_checker = make_format_checker(format_opts)

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

    def get_validator(
        self,
        instance_filename: str,
        instance_doc: t.Dict[str, t.Any],
        format_opts: FormatOptions,
    ):
        self._validator = self.make_validator(format_opts)
        return self._validator


class BuiltinSchemaLoader(SchemaLoader):
    def __init__(self, schema_name: str) -> None:
        self.schema_name = schema_name

    def get_schema_ref_base(self) -> t.Optional[str]:
        return None

    def get_schema(self) -> t.Dict[str, t.Any]:
        return get_builtin_schema(self.schema_name)


class MetaSchemaLoader(SchemaLoaderBase):
    def get_validator(
        self,
        instance_filename: str,
        instance_doc: t.Dict[str, t.Any],
        format_opts: FormatOptions,
    ):
        validator = jsonschema.validators.validator_for(instance_doc)
        return validator(validator.META_SCHEMA)


def schema_loader_from_args(args) -> SchemaLoaderBase:
    if args.schemafile is not None:
        return SchemaLoader(
            args.schemafile,
            args.cache_filename,
            args.no_cache,
        )
    elif args.builtin_schema:
        return BuiltinSchemaLoader(args.builtin_schema)
    else:
        return MetaSchemaLoader()
