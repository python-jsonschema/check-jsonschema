from __future__ import annotations

import enum

import click

from ..formats import FormatOptions, RegexFormatBehavior
from ..transforms import Transform


class SchemaLoadingMode(enum.Enum):
    filepath = "filepath"
    builtin = "builtin"
    metaschema = "metaschema"


class ParseResult:
    def __init__(self) -> None:
        # primary options: schema + instances
        self.schema_mode: SchemaLoadingMode = SchemaLoadingMode.filepath
        self.schema_path: str | None = None
        self.instancefiles: tuple[str, ...] = ()
        # cache controls
        self.disable_cache: bool = False
        self.cache_filename: str | None = None
        # filetype detection (JSON, YAML, TOML, etc)
        self.default_filetype: str = "json"
        # data-transform (for Azure Pipelines and potentially future transforms)
        self.data_transform: Transform | None = None
        # fill default values on instances during validation
        self.fill_defaults: bool = False
        # regex format options
        self.disable_all_formats: bool = False
        self.disable_formats: tuple[str, ...] = ()
        self.format_regex: RegexFormatBehavior = RegexFormatBehavior.default
        # error and output controls
        self.verbosity: int = 1
        self.traceback_mode: str = "short"
        self.output_format: str = "text"

    def set_schema(
        self, schemafile: str | None, builtin_schema: str | None, check_metaschema: bool
    ) -> None:
        mutex_arg_count = sum(
            1 if x else 0 for x in (schemafile, builtin_schema, check_metaschema)
        )
        if mutex_arg_count == 0:
            raise click.UsageError(
                "Either --schemafile, --builtin-schema, or --check-metaschema "
                "must be provided"
            )
        if mutex_arg_count > 1:
            raise click.UsageError(
                "--schemafile, --builtin-schema, and --check-metaschema "
                "are mutually exclusive"
            )

        if schemafile:
            self.schema_mode = SchemaLoadingMode.filepath
            self.schema_path = schemafile
        elif builtin_schema:
            self.schema_mode = SchemaLoadingMode.builtin
            self.schema_path = builtin_schema
        else:
            self.schema_mode = SchemaLoadingMode.metaschema

    @property
    def format_opts(self) -> FormatOptions:
        return FormatOptions(
            enabled=not self.disable_all_formats,
            regex_behavior=self.format_regex,
            disabled_formats=self.disable_formats,
        )
