from __future__ import annotations

import enum
import textwrap

import click

from .catalog import CUSTOM_SCHEMA_NAMES, SCHEMA_CATALOG
from .checker import SchemaChecker
from .formats import FormatOptions, RegexFormatBehavior
from .loaders import (
    BuiltinSchemaLoader,
    InstanceLoader,
    MetaSchemaLoader,
    SchemaLoader,
    SchemaLoaderBase,
)
from .transforms import TRANSFORM_LIBRARY, TransformT

BUILTIN_SCHEMA_NAMES = [f"vendor.{k}" for k in SCHEMA_CATALOG.keys()] + [
    f"custom.{k}" for k in CUSTOM_SCHEMA_NAMES
]
BUILTIN_SCHEMA_CHOICES = (
    BUILTIN_SCHEMA_NAMES + list(SCHEMA_CATALOG.keys()) + CUSTOM_SCHEMA_NAMES
)


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
        # filetype detection (JSON vs YAML)
        self.default_filetype: str | None = None
        # data-transform (for Azure Pipelines and potentially future transforms)
        self.data_transform: TransformT | None = None
        # regex format options
        self.disable_format: bool = False
        self.format_regex: RegexFormatBehavior = RegexFormatBehavior.default
        # error and output controls
        self.show_all_validation_errors: bool = False
        self.traceback_mode: str = "short"

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
            enabled=not self.disable_format, regex_behavior=self.format_regex
        )


@click.command(
    "check-jsonschema",
    help="""\
Check JSON and YAML files against a JSON Schema.

The schema is specified either with '--schemafile' or with '--builtin-schema'.

'check-jsonschema' supports and checks the following formats by default:
    date, email, ipv4, regex, uuid

\b
For the "regex" format, there are multiple modes which can be specified with
'--format-regex':
    default  |  best effort check
    disabled |  do not check the regex format
    python   |  check that the string is a valid python regex

\b
The '--builtin-schema' flag supports the following schema names:
"""
    + textwrap.indent(
        "\n".join(
            textwrap.wrap(
                ", ".join(BUILTIN_SCHEMA_NAMES),
                width=75,
                break_long_words=False,
                break_on_hyphens=False,
            ),
        ),
        "    ",
    ),
)
@click.option(
    "--schemafile",
    help=(
        "The path to a file containing the JSON Schema to use or an "
        "HTTP(S) URI for the schema. If a remote file is used, "
        "it will be downloaded and cached locally based on mtime."
    ),
)
@click.option(
    "--builtin-schema",
    help="The name of an internal schema to use for '--schemafile'",
    type=click.Choice(BUILTIN_SCHEMA_CHOICES, case_sensitive=False),
    metavar="BUILTIN_SCHEMA_NAME",
)
@click.option(
    "--check-metaschema",
    is_flag=True,
    help=(
        "Instead of validating the instances against a schema, treat each file as a "
        "schema and validate them under ther matching metaschemas."
    ),
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable schema caching. Always download remote schemas.",
)
@click.option(
    "--cache-filename",
    help=(
        "The name to use for caching a remote schema. "
        "Defaults to the last slash-delimited part of the URI."
    ),
)
@click.option(
    "--disable-format", is_flag=True, help="Disable all format checks in the schema."
)
@click.option(
    "--format-regex",
    help=(
        "Set the mode of format validation for regexes. "
        "If '--disable-format' is used, this option has no effect."
    ),
    default=RegexFormatBehavior.default.value,
    type=click.Choice([x.value for x in RegexFormatBehavior], case_sensitive=False),
)
@click.option(
    "--default-filetype",
    help="A default filetype to assume when a file is not detected as JSON or YAML",
    type=click.Choice(("json", "yaml"), case_sensitive=True),
)
@click.option(
    "--show-all-validation-errors",
    is_flag=True,
    help=(
        "On validation errors, show all of the underlying errors which occurred. "
        "These may be useful when oneOf or anyOf is used in the schema."
    ),
)
@click.option(
    "--traceback-mode",
    help=(
        "Set the mode of presentation for error traces. "
        "Defaults to shortened tracebacks."
    ),
    type=click.Choice(("full", "short")),
    default="short",
)
@click.option(
    "--data-transform",
    help=(
        "Select a builtin transform which should be applied to instancefiles before "
        "they are checked."
    ),
    type=click.Choice(TRANSFORM_LIBRARY.keys()),
)
@click.argument("instancefiles", required=True, nargs=-1)
def main(
    *,
    schemafile: str | None,
    builtin_schema: str | None,
    check_metaschema: bool,
    no_cache: bool,
    cache_filename: str | None,
    disable_format: bool,
    format_regex: str,
    default_filetype: str | None,
    show_all_validation_errors: bool,
    traceback_mode: str,
    data_transform: str | None,
    instancefiles: tuple[str, ...],
):
    args = ParseResult()

    args.set_schema(schemafile, builtin_schema, check_metaschema)
    args.instancefiles = instancefiles

    args.disable_format = disable_format
    args.format_regex = RegexFormatBehavior(format_regex)
    args.disable_cache = no_cache
    if cache_filename is not None:
        args.cache_filename = cache_filename
    if default_filetype is not None:
        args.default_filetype = default_filetype
    if data_transform is not None:
        args.data_transform = TRANSFORM_LIBRARY[data_transform]
    args.show_all_validation_errors = show_all_validation_errors
    args.traceback_mode = traceback_mode

    execute(args)


# separate parsing from execution for simpler mocking for unit tests


def build_schema_loader(args: ParseResult) -> SchemaLoaderBase:
    if args.schema_mode == SchemaLoadingMode.metaschema:
        return MetaSchemaLoader()
    elif args.schema_mode == SchemaLoadingMode.builtin:
        assert args.schema_path is not None
        return BuiltinSchemaLoader(args.schema_path)
    elif args.schema_mode == SchemaLoadingMode.filepath:
        assert args.schema_path is not None
        return SchemaLoader(args.schema_path, args.cache_filename, args.disable_cache)
    else:
        raise NotImplementedError("no valid schema option provided")


def build_instance_loader(args: ParseResult) -> InstanceLoader:
    return InstanceLoader(
        args.instancefiles,
        default_filetype=args.default_filetype,
        data_transform=args.data_transform,
    )


def build_checker(args: ParseResult) -> SchemaChecker:
    schema_loader = build_schema_loader(args)
    instance_loader = build_instance_loader(args)
    return SchemaChecker(
        schema_loader,
        instance_loader,
        format_opts=args.format_opts,
        traceback_mode=args.traceback_mode,
        show_all_errors=args.show_all_validation_errors,
    )


def execute(args: ParseResult) -> None:
    checker = build_checker(args)
    ret = checker.run()
    if ret == 0:
        click.echo("ok -- validation done")
    click.get_current_context().exit(ret)
