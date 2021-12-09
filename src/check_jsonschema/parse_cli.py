import argparse


# support passing through an argparser class to support tests
def get_parser(cls=None):
    parser = cls() if cls is not None else argparse.ArgumentParser()
    parser.add_argument(
        "--schemafile",
        help=(
            "The path to a file containing the jsonschema to use or an "
            "HTTP(S) URI for the schema. If a remote file is used, "
            "it will be downloaded and cached locally based on mtime. "
            "This option is required unless --builtin-schema is passed."
        ),
    )
    parser.add_argument(
        "--builtin-schema",
        help=(
            "The name of an internal schema to use for `--schemafile`. "
            "Schema names can be found in project documentation."
        ),
    )
    parser.add_argument(
        "--failover-builtin-schema",
        help=(
            "Failover to a specific builtin schema if the schemafile is remote and "
            "cannot be fetched."
        ),
        type=str.lower,
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
        help="Disable all format checks in the schema. "
        "Because JSON Schema does not require that the format property do any "
        "validation, files which validate with other tools may fail to validate "
        "without this flag.",
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
        "--traceback-mode",
        help=(
            "Set the mode of presentation for error traces. "
            "Defaults to shortened tracebacks."
        ),
        type=str.lower,
        default="short",
        choices=("full", "short"),
    )
    parser.add_argument("instancefiles", nargs="+", help="JSON or YAML files to check.")
    return parser


def parse_args(args=None, cls=None):
    parser = get_parser(cls=cls)
    args = parser.parse_args(args)
    if args.schemafile and args.builtin_schema:
        parser.error("--schemafile and --builtin-schema are mutually exclusive")
    if not args.schemafile:
        if not args.builtin_schema:
            parser.error("Either --schemafile or --builtin-schema must be provided")
        if args.failover_builtin_schema:
            parser.error(
                "--failover-builtin-schema is incompatible with --builtin-schema"
            )
    return args
