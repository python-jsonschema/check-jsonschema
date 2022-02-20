import argparse
import textwrap

from .catalog import SCHEMA_CATALOG
from .formats import RegexFormatBehavior
from .transforms import TRANFORM_LIBRARY

_CUSTOM_SCHEMA_NAMES = ["github-workflows-require-timeout"]
BUILTIN_SCHEMA_NAMES = [f"vendor.{k}" for k in SCHEMA_CATALOG.keys()] + [
    f"custom.{k}" for k in _CUSTOM_SCHEMA_NAMES
]
BUILTIN_SCHEMA_CHOICES = (
    BUILTIN_SCHEMA_NAMES + list(SCHEMA_CATALOG.keys()) + _CUSTOM_SCHEMA_NAMES
)


# support passing through an argparser class to support tests
def get_parser(cls=None):
    parser_cls = cls if cls is not None else argparse.ArgumentParser
    parser = parser_cls(
        description="""\
Check JSON and YAML files against a JSON Schema.

The schema is specified either with '--schemafile' or with '--builtin-schema'.

'check-jsonschema' supports and checks the following formats by default:
  date, email, ipv4, regex, uuid
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
For the "regex" format, there are multiple modes which can be specified with
'--format-regex':
    default  |  best effort check
    disabled |  do not check the regex format
    python   |  check that the string is a valid python regex

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
    parser.add_argument(
        "--schemafile",
        help=(
            "The path to a file containing the JSON Schema to use or an "
            "HTTP(S) URI for the schema. If a remote file is used, "
            "it will be downloaded and cached locally based on mtime."
        ),
    )
    parser.add_argument(
        "--builtin-schema",
        help=("The name of an internal schema to use for '--schemafile'"),
        type=str.lower,
        choices=BUILTIN_SCHEMA_CHOICES,
        metavar="BUILTIN_SCHEMA_NAME",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        default=False,
        help="Disable schema caching. Always download remote schemas.",
    )
    parser.add_argument(
        "--disable-format",
        action="store_true",
        default=False,
        help="Disable all format checks in the schema.",
    )
    parser.add_argument(
        "--format-regex",
        help=(
            "Set the mode of format validation for regexes. "
            "If '--disable-format' is used, this option has no effect."
        ),
        type=str.lower,
        default=RegexFormatBehavior.default.value,
        choices=[x.value for x in RegexFormatBehavior],
    )
    parser.add_argument(
        "--cache-filename",
        help=(
            "The name to use for caching a remote schema. "
            "Defaults to the last slash-delimited part of the URI."
        ),
    )
    parser.add_argument(
        "--default-filetype",
        help=(
            "A default filetype to assume when a file is not detected as JSON or YAML"
        ),
        type=str.lower,
        choices=("json", "yaml"),
    )
    parser.add_argument(
        "--show-all-validation-errors",
        action="store_true",
        default=False,
        help=(
            "On validation errors, show all of the underlying errors which occurred. "
            "These may be useful when oneOf or anyOf is used in the schema."
        ),
    )
    parser.add_argument(
        "--traceback-mode",
        help=(
            "Set the mode of presentation for error traces. "
            "Defaults to shortened tracebacks."
        ),
        type=str.lower,
        default="short",
        choices=("full", "short"),
    )
    parser.add_argument(
        "--data-transform",
        help=(
            "Select a builtin transform which should be applied to instancefiles before "
            "they are checked."
        ),
        type=str.lower,
        choices=TRANFORM_LIBRARY.keys(),
    )
    parser.add_argument("instancefiles", nargs="+", help="JSON or YAML files to check.")
    return parser


def parse_args(args=None, cls=None):
    parser = get_parser(cls=cls)
    args = parser.parse_args(args)
    if args.schemafile and args.builtin_schema:
        parser.error("--schemafile and --builtin-schema are mutually exclusive")
    if not (args.schemafile or args.builtin_schema):
        parser.error("Either --schemafile or --builtin-schema must be provided")
    args.format_regex = RegexFormatBehavior(args.format_regex)
    if args.data_transform:
        args.data_transform = TRANFORM_LIBRARY[args.data_transform]
    return args
