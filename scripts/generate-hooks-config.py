#!/usr/bin/env python3
from __future__ import annotations

from check_jsonschema.catalog import SCHEMA_CATALOG


def iter_catalog_hooks():
    for name in SCHEMA_CATALOG:
        # copy config (new dict)
        config = dict(SCHEMA_CATALOG[name]["hook_config"])
        # set computed attributes
        config["schema_name"] = name
        config["id"] = f"check-{name}"
        config["description"] = (
            config.get("description")
            or f"{config['name']} against the schema provided by SchemaStore"
        )
        if "types" in config and isinstance(config["types"], str):
            config["types"] = [config["types"]]
        yield config


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


def format_hook(config) -> str:
    add_args = " ".join(config.get("add_args", []))
    if add_args:
        add_args = " " + add_args
    if isinstance(config["files"], list):
        config[
            "files"
        ] = r""">
    (?x)^(
      {}
    )$""".format(
            "|\n      ".join(config["files"])
        )

    config_str = f"""\
- id: {config["id"]}
  name: {config["name"]}
  description: '{config["description"]}'
  entry: check-jsonschema --builtin-schema vendor.{config["schema_name"]}{add_args}
  language: python
  files: {config["files"]}
"""
    if "types" in config:
        config_str += f"""\
  types: [{','.join(config['types'])}]
"""
    return config_str


def generate_hook_config() -> str:
    return "\n".join(format_hook(h) for h in iter_catalog_hooks())


def update_readme_list_schemas() -> None:
    print("updating README.md -- list schemas")
    with open("README.md") as fp:
        content = fp.read()

    vendored_list_start = "<!-- vendored-schema-list-start -->"
    vendored_list_end = "<!-- vendored-schema-list-end -->"

    content_head = content.split(vendored_list_start)[0]
    content_tail = content.split(vendored_list_end)[-1]

    generated_list = "\n".join(
        [vendored_list_start]
        + [f"- `vendor.{n}`" for n in SCHEMA_CATALOG]
        + [vendored_list_end]
    )

    content = content_head + generated_list + content_tail
    with open("README.md", "w") as fp:
        fp.write(content)


def update_readme_supported_hooks() -> None:
    print("updating README.md -- generated hooks")
    with open("README.md") as fp:
        content = fp.read()

    generated_list_start = "<!-- generated-hook-list-start -->"
    generated_list_end = "<!-- generated-hook-list-end -->"

    content_head = content.split(generated_list_start)[0]
    content_tail = content.split(generated_list_end)[-1]

    generated_list = "\n".join(
        [generated_list_start]
        + [
            f"- {config['id']}:\n    {config['description']}"
            for config in iter_catalog_hooks()
        ]
        + [generated_list_end]
    )

    content = content_head + generated_list + content_tail
    with open("README.md", "w") as fp:
        fp.write(content)


def update_readme() -> None:
    update_readme_list_schemas()
    update_readme_supported_hooks()


def main() -> None:
    update_hook_config(generate_hook_config())
    update_readme()


if __name__ == "__main__":
    main()
