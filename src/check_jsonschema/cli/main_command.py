from __future__ import annotations

import os
import textwrap

import click

from ..catalog import CUSTOM_SCHEMA_NAMES, SCHEMA_CATALOG
from ..checker import SchemaChecker
from ..formats import KNOWN_FORMATS, RegexFormatBehavior
from ..instance_loader import InstanceLoader
from ..parsers import SUPPORTED_FILE_FORMATS
from ..reporter import REPORTER_BY_NAME, Reporter
from ..schema_loader import (
    BuiltinSchemaLoader,
    MetaSchemaLoader,
    SchemaLoader,
    SchemaLoaderBase,
)
from ..transforms import TRANSFORM_LIBRARY
from .param_types import CommaDelimitedList
from .parse_result import ParseResult, SchemaLoadingMode
from .warnings import deprecation_warning_callback

BUILTIN_SCHEMA_NAMES = [f"vendor.{k}" for k in SCHEMA_CATALOG.keys()] + [
    f"custom.{k}" for k in CUSTOM_SCHEMA_NAMES
]
BUILTIN_SCHEMA_CHOICES = (
    BUILTIN_SCHEMA_NAMES + list(SCHEMA_CATALOG.keys()) + CUSTOM_SCHEMA_NAMES
)


def set_color_mode(ctx: click.Context, param: str, value: str) -> None:
    if "NO_COLOR" in os.environ:
        ctx.color = False
    else:
        ctx.color = {
            "auto": None,
            "always": True,
            "never": False,
        }[value]


def pretty_helptext_list(values: list[str] | tuple[str, ...]) -> str:
    return textwrap.indent(
        "\n".join(
            textwrap.wrap(
                ", ".join(values),
                width=75,
                break_long_words=False,
                break_on_hyphens=False,
            ),
        ),
        "    ",
    )


@click.command(
    "check-jsonschema",
    help="""\
Check JSON and YAML files against a JSON Schema.

The schema is specified either with '--schemafile' or with '--builtin-schema'.

'check-jsonschema' supports format checks with appropriate libraries installed,
including the following formats by default:
    date, email, ipv4, ipv6, regex, uuid

\b
For the "regex" format, there are multiple modes which can be specified with
'--format-regex':
    default  |  best effort check
    disabled |  do not check the regex format
    python   |  check that the string is a valid python regex

\b
The '--builtin-schema' flag supports the following schema names:
"""
    + pretty_helptext_list(BUILTIN_SCHEMA_NAMES)
    + """\

\b
The '--disable-formats' flag supports the following formats:
"""
    + pretty_helptext_list(KNOWN_FORMATS),
)
@click.help_option("-h", "--help")
@click.version_option()
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
        "schema and validate them under their matching metaschemas."
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
    "--disable-format",
    is_flag=True,
    help="{deprecated} Disable all format checks in the schema.",
    callback=deprecation_warning_callback(
        "--disable-format",
        is_flag=True,
        append_message="Users should now pass '--disable-formats \"*\"' for "
        "the same functionality.",
    ),
)
@click.option(
    "--disable-formats",
    multiple=True,
    help="Disable specific format checks in the schema. "
    "Pass '*' to disable all format checks.",
    type=CommaDelimitedList(choices=("*", *KNOWN_FORMATS)),
    metavar="{*|FORMAT,FORMAT,...}",
)
@click.option(
    "--format-regex",
    help=(
        "Set the mode of format validation for regexes. "
        "If `--disable-formats regex` is used, this option has no effect."
    ),
    default=RegexFormatBehavior.default.value,
    type=click.Choice([x.value for x in RegexFormatBehavior], case_sensitive=False),
)
@click.option(
    "--default-filetype",
    help="A default filetype to assume when a file's type is not detected",
    default="json",
    show_default=True,
    type=click.Choice(SUPPORTED_FILE_FORMATS, case_sensitive=True),
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
    type=click.Choice(tuple(TRANSFORM_LIBRARY.keys())),
)
@click.option(
    "--fill-defaults",
    help="Autofill 'default' values prior to validation.",
    is_flag=True,
)
@click.option(
    "-o",
    "--output-format",
    help="Which output format to use",
    type=click.Choice(tuple(REPORTER_BY_NAME.keys()), case_sensitive=False),
    default="text",
)
@click.option(
    "--color",
    help="Force or disable colorized output. Defaults to autodetection.",
    default="auto",
    type=click.Choice(("auto", "always", "never")),
    callback=set_color_mode,
    expose_value=False,
)
@click.option(
    "-v",
    "--verbose",
    help=(
        "Increase output verbosity. On validation errors, this may be especially "
        "useful when oneOf or anyOf is used in the schema."
    ),
    count=True,
)
@click.option(
    "-q",
    "--quiet",
    help="Reduce output verbosity",
    count=True,
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
    disable_formats: tuple[list[str], ...],
    format_regex: str,
    default_filetype: str,
    traceback_mode: str,
    data_transform: str | None,
    fill_defaults: bool,
    output_format: str,
    verbose: int,
    quiet: int,
    instancefiles: tuple[str, ...],
) -> None:
    args = ParseResult()

    args.set_schema(schemafile, builtin_schema, check_metaschema)
    args.instancefiles = instancefiles

    normalized_disable_formats: tuple[str, ...] = tuple(
        f for sublist in disable_formats for f in sublist
    )
    if disable_format or "*" in normalized_disable_formats:
        args.disable_all_formats = True
    else:
        args.disable_formats = normalized_disable_formats
    args.format_regex = RegexFormatBehavior(format_regex)
    args.disable_cache = no_cache
    args.default_filetype = default_filetype
    args.fill_defaults = fill_defaults
    if cache_filename is not None:
        args.cache_filename = cache_filename
    if data_transform is not None:
        args.data_transform = TRANSFORM_LIBRARY[data_transform]

    # verbosity behavior:
    # - default is 1
    # - count '-v'
    # - subtract count of '-q'
    args.verbosity = 1 + verbose - quiet
    args.traceback_mode = traceback_mode
    args.output_format = output_format

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


def build_reporter(args: ParseResult) -> Reporter:
    cls = REPORTER_BY_NAME[args.output_format]
    return cls(verbosity=args.verbosity)


def build_checker(args: ParseResult) -> SchemaChecker:
    schema_loader = build_schema_loader(args)
    instance_loader = build_instance_loader(args)
    reporter = build_reporter(args)
    return SchemaChecker(
        schema_loader,
        instance_loader,
        reporter,
        format_opts=args.format_opts,
        traceback_mode=args.traceback_mode,
        fill_defaults=args.fill_defaults,
    )


def execute(args: ParseResult) -> None:
    checker = build_checker(args)
    ret = checker.run()
    click.get_current_context().exit(ret)
