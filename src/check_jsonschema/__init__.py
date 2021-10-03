import argparse
import sys

import jsonschema

from .loaders import InstanceLoader, SchemaLoader


def main():
    parser = argparse.ArgumentParser()
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
    args = parser.parse_args()

    schema_loader = SchemaLoader(args.schemafile, args.cache_filename, args.no_cache)
    validator = schema_loader.get_validator()

    instances = InstanceLoader(args.instancefiles)

    failures = {}
    for filename, doc in instances.iter_files():
        try:
            validator.validate(instance=doc)
        except jsonschema.ValidationError as err:
            failures[filename] = err
    if failures:
        print("Schema validation errors were encountered.")
        for filename, err in failures.items():
            path = [str(x) for x in err.path] or ["<root>"]
            path = ".".join(x if "." not in x else f'"{x}"' for x in path)
            print(f"  \033[0;33m{filename}::{path}: \033[0m{err.message}")
        sys.exit(1)

    print("ok -- validation done")
