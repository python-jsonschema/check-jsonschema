from __future__ import annotations

import pathlib
import typing as t
import urllib.error
import urllib.parse

import jsonschema

from ..builtin_schemas import get_builtin_schema
from ..formats import FormatOptions, make_format_checker
from ..utils import is_url_ish
from .errors import UnsupportedUrlScheme
from .readers import HttpSchemaReader, LocalSchemaReader
from .resolver import make_ref_resolver


def _extend_with_default(
    validator_class: type[jsonschema.Validator],
) -> type[jsonschema.Validator]:
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults_then_validate(
        validator: jsonschema.Validator,
        properties: dict[str, dict[str, t.Any]],
        instance: dict[str, t.Any],
        schema: dict[str, t.Any],
    ) -> t.Iterator[jsonschema.ValidationError]:
        for property_name, subschema in properties.items():
            if "default" in subschema and property_name not in instance:
                instance[property_name] = subschema["default"]

        yield from validate_properties(
            validator,
            properties,
            instance,
            schema,
        )

    return jsonschema.validators.extend(
        validator_class,
        {"properties": set_defaults_then_validate},
    )


class SchemaLoaderBase:
    def get_validator(
        self,
        path: pathlib.Path,
        instance_doc: dict[str, t.Any],
        format_opts: FormatOptions,
        fill_defaults: bool,
    ) -> jsonschema.Validator:
        raise NotImplementedError


class SchemaLoader(SchemaLoaderBase):
    def __init__(
        self,
        schemafile: str,
        cache_filename: str | None = None,
        disable_cache: bool = False,
    ) -> None:
        # record input parameters (these are not to be modified)
        self.schemafile = schemafile
        self.cache_filename = cache_filename
        self.disable_cache = disable_cache

        # if the schema location is a URL, which may include a file:// URL, parse it
        self.url_info = None
        if is_url_ish(self.schemafile):
            self.url_info = urllib.parse.urlparse(self.schemafile)

        # setup a schema reader lazily, when needed
        self._reader: LocalSchemaReader | HttpSchemaReader | None = None

    @property
    def reader(self) -> LocalSchemaReader | HttpSchemaReader:
        if self._reader is None:
            self._reader = self._get_schema_reader()
        return self._reader

    def _get_schema_reader(self) -> LocalSchemaReader | HttpSchemaReader:
        if self.url_info is None or self.url_info.scheme in ("file", ""):
            return LocalSchemaReader(self.schemafile)

        if self.url_info.scheme in ("http", "https"):
            return HttpSchemaReader(
                self.schemafile,
                self.cache_filename,
                self.disable_cache,
            )
        else:
            raise UnsupportedUrlScheme(
                "check-jsonschema only supports http, https, and local files. "
                f"detected parsed URL had an unrecognized scheme: {self.url_info}"
            )

    def get_schema_ref_base(self) -> str | None:
        return self.reader.get_ref_base()

    def get_schema(self) -> dict[str, t.Any]:
        return self.reader.read_schema()

    def get_validator(
        self,
        path: pathlib.Path,
        instance_doc: dict[str, t.Any],
        format_opts: FormatOptions,
        fill_defaults: bool,
    ) -> jsonschema.Validator:
        schema_uri = self.get_schema_ref_base()
        schema = self.get_schema()

        schema_dialect = schema.get("$schema")

        # format checker (which may be None)
        format_checker = make_format_checker(format_opts, schema_dialect)

        # ref resolver which may be built from the schema path
        # if the location is a URL, there's no change, but if it's a file path
        # it's made absolute and URI-ized
        # the resolver should use `$id` if there is one present in the schema
        ref_resolver = make_ref_resolver(schema_uri, schema)

        # get the correct validator class and check the schema under its metaschema
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)

        # extend the validator class with default-filling behavior if appropriate
        if fill_defaults:
            validator_cls = _extend_with_default(validator_cls)

        # now that we know it's safe to try to create the validator instance, do it
        validator = validator_cls(
            schema,
            resolver=ref_resolver,
            format_checker=format_checker,
        )
        return t.cast(jsonschema.Validator, validator)


class BuiltinSchemaLoader(SchemaLoader):
    def __init__(self, schema_name: str) -> None:
        self.schema_name = schema_name

    def get_schema_ref_base(self) -> str | None:
        return None

    def get_schema(self) -> dict[str, t.Any]:
        return get_builtin_schema(self.schema_name)


class MetaSchemaLoader(SchemaLoaderBase):
    def get_validator(
        self,
        path: pathlib.Path,
        instance_doc: dict[str, t.Any],
        format_opts: FormatOptions,
        fill_defaults: bool,
    ) -> jsonschema.Validator:
        schema_validator = jsonschema.validators.validator_for(instance_doc)
        meta_validator_class = jsonschema.validators.validator_for(
            schema_validator.META_SCHEMA, default=schema_validator
        )

        # format checker (which may be None)
        meta_schema_dialect = schema_validator.META_SCHEMA.get("$schema")
        format_checker = make_format_checker(format_opts, meta_schema_dialect)

        meta_validator = meta_validator_class(
            schema_validator.META_SCHEMA, format_checker=format_checker
        )
        return meta_validator
