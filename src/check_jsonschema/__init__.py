import sys

import jsonschema

from .loaders import InstanceLoader, SchemaLoader
from .parse_cli import parse_args


def main():
    args = parse_args()

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
