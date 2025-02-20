#!/usr/bin/env python3
from __future__ import annotations

import datetime
import hashlib
import os
import re
import subprocess
import textwrap

import requests

from check_jsonschema.catalog import SCHEMA_CATALOG

TODAY = datetime.datetime.today().strftime("%Y-%m-%d")

VENDOR_SLUG = "\n.. vendor-insert-here\n"

EXISTING_CHANGELINE_PATTERN = re.compile(
    re.escape(VENDOR_SLUG)
    + "\n?- Update vendored schemas: "
    + r"([\w-]+(,\s+[\w-]+)*) "
    + r"\(\d{4}-\d{2}-\d{2}\)"
    + "\n",
    flags=re.MULTILINE,
)

OLD_HASHES: dict[str, str] = {}
UPDATED_SCHEMAS: set[str] = set()
SCHEMAS_WITH_NEW_HASHES: set[str] = set()


def schema2filename(name: str) -> str:
    return f"src/check_jsonschema/builtin_schemas/vendor/{name}.json"


def schema2hashfile(name: str) -> str:
    return f"src/check_jsonschema/builtin_schemas/vendor/sha256/{name}.sha256"


def file2digest(filepath: str) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as fp:
        sha.update(fp.read())
    return sha.hexdigest()


def load_old_hashes() -> None:
    for name, _config in SCHEMA_CATALOG.items():
        hashfile = schema2hashfile(name)
        if os.path.exists(hashfile):
            with open(hashfile) as fp:
                OLD_HASHES[name] = fp.read().strip()


def normalize_schema_contents(data: bytes) -> bytes:
    lines = data.split(b"\n")
    return b"\n".join(line.rstrip(b" ") for line in lines)


def download_schemas() -> None:
    print("downloading schemas to check for updates")
    session = requests.Session()

    for schema_name, config in SCHEMA_CATALOG.items():
        schema_url = config["url"]

        print(f"  {schema_name} ({schema_url})")
        res = session.get(schema_url)
        new_content = normalize_schema_contents(res.content)

        sha = hashlib.sha256()
        sha.update(new_content)
        new_digest = sha.hexdigest()

        # early abort if downloaded content matches old hash
        if new_digest == OLD_HASHES.get(schema_name):
            continue

        with open(schema2filename(schema_name), "wb") as fp:
            fp.write(new_content)
        UPDATED_SCHEMAS.add(schema_name)


def run_precommit() -> None:
    if not UPDATED_SCHEMAS:
        print("no downloads updated, skipping pre-commit")
        return

    print("running pre-commit")
    cmd = ["pre-commit", "run", "--files"]
    for name in UPDATED_SCHEMAS:
        cmd.append(schema2filename(name))
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode == 0:
        return


def save_new_hashes() -> None:
    print("saving new hashes")

    def _save_new_hash(name: str, digest: str) -> None:
        print(f"  - new hash for '{name}'")
        hashfile = schema2hashfile(name)
        with open(hashfile, "w", encoding="utf-8") as fp:
            fp.write(digest)
        SCHEMAS_WITH_NEW_HASHES.add(name)

    for name in UPDATED_SCHEMAS:
        digest = file2digest(schema2filename(name))

        # new file, changes were made and hash should update, OR
        # if the existing hash does not match the new hash, save the new one
        if name not in OLD_HASHES or digest != OLD_HASHES[name]:
            _save_new_hash(name, digest)


def check_changes_made() -> bool:
    return bool(SCHEMAS_WITH_NEW_HASHES)


def update_changelog() -> None:
    print("changes were made, updating changelog")
    with open("CHANGELOG.rst", encoding="utf-8") as fp:
        content = fp.read()

    new_item_prefix = "- Update vendored schemas:"

    if match := EXISTING_CHANGELINE_PATTERN.search(content):
        updated_schemas = {s.rstrip(",") for s in match.group(1).split()}
        updated_schemas.update(SCHEMAS_WITH_NEW_HASHES)
    else:
        updated_schemas = SCHEMAS_WITH_NEW_HASHES

    schema_list = sorted(updated_schemas)
    new_item = new_item_prefix + f" {', '.join(schema_list)} ({TODAY})\n"

    new_item = "\n".join(
        textwrap.wrap(
            new_item, break_on_hyphens=False, subsequent_indent="  ", width=88
        )
    )
    new_item = f"{VENDOR_SLUG}\n{new_item}\n"

    if match:
        content = EXISTING_CHANGELINE_PATTERN.sub(new_item, content)
    else:
        content = content.replace(VENDOR_SLUG, new_item)

    with open("CHANGELOG.rst", "w", encoding="utf-8") as fp:
        fp.write(content)


def main() -> None:
    print("vendor-schemas:BEGIN")
    load_old_hashes()
    download_schemas()
    run_precommit()
    save_new_hashes()
    if check_changes_made():
        update_changelog()
    else:
        print("no changes detected")
    print("vendor-schemas:END")


if __name__ == "__main__":
    main()
