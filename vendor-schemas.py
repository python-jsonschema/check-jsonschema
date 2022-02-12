#!/usr/bin/env python3
import datetime
import hashlib

import requests

from check_jsonschema.catalog import SCHEMA_CATALOG

today = datetime.datetime.today().strftime("%Y-%m-%d")


def download_schema(schema_name, schema_url) -> bool:
    print(f"downloading {schema_name} schema to check ({schema_url})")
    res = requests.get(schema_url)
    sha = hashlib.sha256()
    sha.update(res.content)
    new_digest = sha.hexdigest()

    with open(
        f"src/check_jsonschema/builtin_schemas/vendor/{schema_name}.sha256", "r"
    ) as fp:
        prev_digest = fp.read().strip()

    if new_digest == prev_digest:
        return False

    with open(
        f"src/check_jsonschema/builtin_schemas/vendor/{schema_name}.json", "wb"
    ) as fp:
        fp.write(res.content)
    with open(
        f"src/check_jsonschema/builtin_schemas/vendor/{schema_name}.sha256", "w"
    ) as fp:
        fp.write(new_digest)

    return True


def update_changelog():
    with open("CHANGELOG.md", encoding="utf-8") as fp:
        content = fp.read()
    content = content.replace(
        """
<!-- vendor-insert-here -->
""",
        f"""
<!-- vendor-insert-here -->
- Update vendored schemas ({today})
""",
    )
    with open("CHANGELOG.md", "w", encoding="utf-8") as fp:
        fp.write(content)


def main():
    made_changes = False
    for name, config in SCHEMA_CATALOG.items():
        made_changes = download_schema(name, config["url"]) or made_changes
    if made_changes:
        update_changelog()


if __name__ == "__main__":
    main()
