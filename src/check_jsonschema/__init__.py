import argparse
import json
import sys

import jsonschema
import ruamel.yaml
from identify import identify

from .cachedownloader import CacheDownloader

yaml = ruamel.yaml.YAML(typ="safe")


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
        "--cache-filename",
        help=(
            "The name to use for caching a remote schema. "
            "Defaults to the last slash-delimited part of the URI."
        ),
    )
    parser.add_argument("instancefiles", nargs="+", help="JSON or YAML files to check.")
    args = parser.parse_args()

    if args.schemafile.startswith("https://") or args.schemafile.startswith("http://"):
        cache = CacheDownloader(args.schemafile, args.cache_filename)
        with cache.open() as fp:
            schema = json.load(fp)
    else:
        with open(args.schemafile) as f:
            schema = json.load(f)

    failures = {}
    for instancefile in args.instancefiles:
        tags = identify.tags_from_path(instancefile)
        if "yaml" in tags:
            loader = yaml.load
        elif "json" in tags:
            loader = json.load
        else:
            raise ValueError(
                f"cannot check {instancefile} as it is neither yaml nor json"
            )
        with open(instancefile) as f:
            doc = loader(f)

        try:
            jsonschema.validate(instance=doc, schema=schema)
        except jsonschema.ValidationError as err:
            failures[instancefile] = err
    if failures:
        print("Schema validation errors were encountered.")
        for filename in args.instancefiles:
            if filename in failures:
                err = failures[filename]
                path = [str(x) for x in err.path] or ["<root>"]
                path = ".".join(x if "." not in x else f'"{x}"' for x in path)
                print(f"  \033[0;33m{filename}::{path}: \033[0m{err.message}")
        sys.exit(1)

    print("ok -- validation done")
