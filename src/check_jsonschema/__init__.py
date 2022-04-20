from __future__ import annotations

import textwrap

import click

from .catalog import CUSTOM_SCHEMA_NAMES, SCHEMA_CATALOG
from .checker import SchemaChecker
from .formats import FormatOptions, RegexFormatBehavior
from .loaders import InstanceLoader, schema_loader_from_args
from .transforms import TRANFORM_LIBRARY

BUILTIN_SCHEMA_NAMES = [f"vendor.{k}" for k in SCHEMA_CATALOG.keys()] + [
    f"custom.{k}" for k in CUSTOM_SCHEMA_NAMES
]
BUILTIN_SCHEMA_CHOICES = (
    BUILTIN_SCHEMA_NAMES + list(SCHEMA_CATALOG.keys()) + CUSTOM_SCHEMA_NAMES
)


def _gen_schema_name_list() -> str:
    return textwrap.indent(
        "\n".join(
            textwrap.wrap(
                ", ".join(BUILTIN_SCHEMA_NAMES),
                width=75,
                break_long_words=False,
                break_on_hyphens=False,
            ),
        ),
        "    ",
    )


def _mutex_arg_list(conjunction: str = "and") -> str:
    return f"--schemafile, --builtin-schema, {conjunction} --check-metaschema"


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
    + _gen_schema_name_list(),
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
    "--disable-format",
    is_flag=True,
    help="Disable all format checks in the schema.",
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
    type=click.Choice(TRANFORM_LIBRARY.keys()),
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
    mutex_arg_count = sum(
        1 if x else 0 for x in (schemafile, builtin_schema, check_metaschema)
    )
    if mutex_arg_count == 0:
        raise click.UsageError(f"Either {_mutex_arg_list('or')} must be provided")
    if mutex_arg_count > 1:
        raise click.UsageError(f"{_mutex_arg_list()} are mutually exclusive")

    do_main(
        schemafile=schemafile,
        builtin_schema=builtin_schema,
        check_metaschema=check_metaschema,
        no_cache=no_cache,
        cache_filename=cache_filename,
        disable_format=disable_format,
        format_regex=format_regex,
        default_filetype=default_filetype,
        show_all_validation_errors=show_all_validation_errors,
        traceback_mode=traceback_mode,
        data_transform=data_transform,
        instancefiles=instancefiles,
    )


# separate parsing from execution for simpler mocking for unit tests
def do_main(
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
    schema_loader = schema_loader_from_args(
        schemafile, cache_filename, no_cache, builtin_schema, check_metaschema
    )

    instance_loader = InstanceLoader(
        instancefiles,
        default_filetype=default_filetype,
        data_transform=(
            TRANFORM_LIBRARY[data_transform] if data_transform is not None else None
        ),
    )

    format_opts = FormatOptions(
        enabled=not disable_format,
        regex_behavior=RegexFormatBehavior(format_regex),
    )
    checker = SchemaChecker(
        schema_loader,
        instance_loader,
        format_opts=format_opts,
        traceback_mode=traceback_mode,
        show_all_errors=show_all_validation_errors,
    )
    ret = checker.run()
    if ret == 0:
        print("ok -- validation done")
    click.get_current_context().exit(ret)
