#!/usr/bin/env python3
from __future__ import annotations

from check_jsonschema.catalog import SCHEMA_CATALOG


def update_hook_config(new_config: str) -> None:
    print("updating .pre-commit-hooks.yaml")
    with open(".pre-commit-hooks.yaml") as fp:
        content = fp.read()

    autogen_marker = "# --AUTOGEN_HOOKS_START-- #"

    # get the first part of the content (and assert that it's OK)
    content = content.split(autogen_marker)[0]
    assert "check-jsonschema" in content

    content = content + autogen_marker + "\n\n" + new_config
    with open(".pre-commit-hooks.yaml", "w") as fp:
        fp.write(content)


def format_hook(name: str) -> str:
    config = SCHEMA_CATALOG[name]["hook_config"]
    description = (
        config.get("description")
        or f"{config['name']} against the schema provided by SchemaStore"
    )
    add_args = " ".join(config.get("add_args", []))
    if add_args:
        add_args = " " + add_args
    if isinstance(config["files"], str):
        files = config["files"]
    else:
        files = r""">
    (?x)^(
      {}
    )$""".format(
            "|\n      ".join(config["files"])
        )

    config_str = f"""\
- id: check-{name}
  name: {config["name"]}
  description: '{description}'
  entry: check-jsonschema --builtin-schema vendor.{name}{add_args}
  language: python
  files: {files}
"""
    if "types" in config:
        if isinstance(config["types"], str):
            type_str = config["types"]
        else:
            type_str = ",".join(config["types"])
        config_str += f"""\
  types: [{type_str}]
"""
    return config_str


def generate_hook_config() -> str:
    return "\n".join(format_hook(hookname) for hookname in SCHEMA_CATALOG)


def main() -> None:
    update_hook_config(generate_hook_config())


if __name__ == "__main__":
    main()
