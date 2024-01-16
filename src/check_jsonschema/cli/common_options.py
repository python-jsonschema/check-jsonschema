import os
import typing as t

import click

from ..formats import KNOWN_FORMATS, RegexVariantName
from ..reporter import REPORTER_BY_NAME
from .param_types import CommaDelimitedList, ValidatorClassName

C = t.TypeVar("C", bound=t.Union[t.Callable, click.Command])


def set_color_mode(ctx: click.Context, param: str, value: str) -> None:
    if "NO_COLOR" in os.environ:
        ctx.color = False
    else:
        ctx.color = {
            "auto": None,
            "always": True,
            "never": False,
        }[value]


_color_opt = click.option(
    "--color",
    help="Force or disable colorized output. Defaults to autodetection.",
    default="auto",
    type=click.Choice(("auto", "always", "never")),
    callback=set_color_mode,
    expose_value=False,
)


def _verbosity_opts(cmd: C) -> C:
    cmd = click.option(
        "-v",
        "--verbose",
        help=(
            "Increase output verbosity. On validation errors, this may be especially "
            "useful when oneOf or anyOf is used in the schema."
        ),
        count=True,
    )(cmd)
    cmd = click.option(
        "-q",
        "--quiet",
        help="Reduce output verbosity",
        count=True,
    )(cmd)
    return cmd


_traceback_mode_opt = click.option(
    "--traceback-mode",
    help=(
        "Set the mode of presentation for error traces. "
        "Defaults to shortened tracebacks."
    ),
    type=click.Choice(("full", "short")),
    default="short",
)

output_format_opt = click.option(
    "-o",
    "--output-format",
    help="Which output format to use.",
    type=click.Choice(tuple(REPORTER_BY_NAME.keys()), case_sensitive=False),
    default="text",
)


base_uri_opt = click.option(
    "--base-uri",
    help=(
        "Override the base URI for the schema. The default behavior is to "
        "follow the behavior specified by the JSON Schema spec, which is to "
        "prefer an explicit '$id' and failover to the retrieval URI."
    ),
)


def download_opts(cmd: C) -> C:
    cmd = click.option(
        "--no-cache",
        is_flag=True,
        help="Disable schema caching. Always download remote schemas.",
    )(cmd)
    cmd = click.option(
        "--cache-filename",
        help=(
            "The name to use for caching a remote schema when downloaded. "
            "Defaults to the last slash-delimited part of the URI."
        ),
    )(cmd)
    return cmd


def validator_behavior_opts(cmd: C) -> C:
    cmd = click.option(
        "--fill-defaults",
        help=(
            "Autofill 'default' values prior to validation. "
            "This may conflict with certain third-party validators used with "
            "'--validator-class'"
        ),
        is_flag=True,
    )(cmd)
    cmd = click.option(
        "--validator-class",
        help=(
            "The fully qualified name of a python validator to use in place of "
            "the 'jsonschema' library validators, in the form of '<package>:<class>'. "
            "The validator must be importable in the same environment where "
            "'check-jsonschema' is run."
        ),
        type=ValidatorClassName(),
    )(cmd)
    return cmd


def jsonschema_format_opts(cmd: C) -> C:
    cmd = click.option(
        "--disable-formats",
        multiple=True,
        help="Disable specific format checks in the schema. "
        "Pass '*' to disable all format checks.",
        type=CommaDelimitedList(choices=("*", *KNOWN_FORMATS)),
        metavar="{*|FORMAT,FORMAT,...}",
    )(cmd)
    cmd = click.option(
        "--format-regex",
        help=(
            "Set the mode of format validation for regexes. "
            "If `--disable-formats regex` is used, this option has no effect."
        ),
        default=RegexVariantName.default.value,
        type=click.Choice([x.value for x in RegexVariantName], case_sensitive=False),
    )(cmd)
    return cmd


def universal_opts(cmd: C) -> C:
    cmd = _traceback_mode_opt(cmd)
    cmd = _color_opt(cmd)
    cmd = _verbosity_opts(cmd)
    cmd = click.help_option("-h", "--help")(cmd)
    cmd = click.version_option()(cmd)
    return cmd
