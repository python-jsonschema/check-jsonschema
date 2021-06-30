import argparse
import contextlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time
import urllib.request

import jsonschema
import ruamel.yaml
from identify import identify

yaml = ruamel.yaml.YAML(typ="safe")


sysname = platform.system()
# on windows, try to get the appdata env var
# this *could* result in CACHE_DIR=None, which is fine, just skip caching in
# that case
if sysname == "Windows":
    CACHE_DIR = os.getenv("LOCALAPPDATA", os.getenv("APPDATA"))
# macOS -> app support dir
elif sysname == "Darwin":
    CACHE_DIR = os.path.expanduser("~/Library/Caches")
# default for unknown platforms, namely linux behavior
# use XDG env var and default to ~/.cache/
else:
    CACHE_DIR = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache/"))

if CACHE_DIR:
    CACHE_DIR = os.path.join(CACHE_DIR, "jsonschema_validate")

LASTMOD_FMT = "%a, %d %b %Y %H:%M:%S %Z"
LASTMOD_DEFAULT = "Sun, 01 Jan 1970 00:00:01 GMT"


@contextlib.contextmanager
def cached_open(file_url, filename):
    if not CACHE_DIR:
        with urllib.request.urlopen(file_url) as fp:
            yield fp
    else:
        try:
            os.makedirs(CACHE_DIR)
        except FileExistsError:
            pass

        if not filename:
            filename = file_url.split("/")[-1]
        dest = os.path.join(CACHE_DIR, filename)

        # connect, but don't read yet
        conn = urllib.request.urlopen(file_url)

        # download and cache to disk based on the mtime of the local file if it
        # exists (check mtime before download for speed) or just download if missing
        do_download = True
        if os.path.exists(dest):
            # get both timestamps as epoch times
            local_mtime = os.path.getmtime(dest)
            remote_mtime = time.mktime(
                time.strptime(
                    conn.headers.get("last-modified", LASTMOD_DEFAULT), LASTMOD_FMT
                )
            )
            do_download = local_mtime < remote_mtime
        if do_download:
            # download to a temp file and then move to the dest
            # this makes the download safe if run in parallel (parallel runs
            # won't create a new empty file for writing and cause failures)
            fp = tempfile.NamedTemporaryFile(mode="wb", delete=False)
            fp.write(conn.read())
            fp.close()
            shutil.copy(fp.name, dest)
            os.remove(fp.name)

        conn.close()

        with open(dest, "r") as fp:
            yield fp


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
        with cached_open(args.schemafile, args.cache_filename) as fp:
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
