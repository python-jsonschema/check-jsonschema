import argparse


# support passing through an argparser class to support tests
def get_parser(cls=None):
    parser = cls() if cls is not None else argparse.ArgumentParser()
    parser.add_argument(
        "--schemafile",
        required=True,
        help=(
            "REQUIRED. "
            "The path to a file containing the jsonschema to use or an "
            "HTTP(S) URI for the schema. If a remote file is used, "
            "it will be downloaded and cached locally based on mtime."
        ),
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        default=False,
        help="Disable schema caching. Always download remote schemas.",
    )
    parser.add_argument(
        "--cache-filename",
        help=(
            "The name to use for caching a remote schema. "
            "Defaults to the last slash-delimited part of the URI."
        ),
    )
    parser.add_argument("instancefiles", nargs="+", help="JSON or YAML files to check.")
    return parser


def parse_args(args=None, cls=None):
    parser = get_parser(cls=cls)
    return parser.parse_args(args)
