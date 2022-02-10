#!/usr/bin/env python3
import datetime
import hashlib
import shlex

import requests
import ruamel.yaml

yaml = ruamel.yaml.YAML(typ="safe")
today = datetime.datetime.today().strftime("%Y-%m-%d")


def entry2schema(entry):
    line = shlex.split(entry)
    try:
        argidx = line.index("--schemafile") + 1
        return line[argidx]
    except (ValueError, IndexError):
        return None


def iter_hook_entries():
    with open(".pre-commit-hooks.yaml") as fp:
        data = yaml.load(fp)
    for hook in data:
        yield (hook["id"], hook["entry"])


def iter_schema_urls():
    for (hook_id, entry) in iter_hook_entries():
        schema = entry2schema(entry)
        if schema is not None and schema.startswith("https://"):
            yield (hook_id, schema)


def download_schema(hookname, schema_url) -> bool:
    res = requests.get(schema_url)
    sha = hashlib.sha256()
    sha.update(res.content)
    new_digest = sha.hexdigest()

    with open(
        f"src/check_jsonschema/builtin_schemas/vendor/{hookname}.sha256", "r"
    ) as fp:
        prev_digest = fp.read().strip()

    if new_digest == prev_digest:
        return False

    with open(
        f"src/check_jsonschema/builtin_schemas/vendor/{hookname}.json", "wb"
    ) as fp:
        fp.write(res.content)
    with open(
        f"src/check_jsonschema/builtin_schemas/vendor/{hookname}.sha256", "w"
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
- update vendored schemas ({today})
""",
    )
    with open("CHANGELOG.md", "w", encoding="utf-8") as fp:
        fp.write(content)


def main():
    made_changes = False
    for hook_id, schema_url in iter_schema_urls():
        hookname = hook_id
        if hookname.startswith("check-"):
            hookname = hookname[6:].replace("_", "-")
        made_changes = made_changes or download_schema(hookname, schema_url)
    if made_changes:
        update_changelog()


if __name__ == "__main__":
    main()
