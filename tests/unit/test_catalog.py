from pathlib import Path

import ruamel.yaml

from check_jsonschema.catalog import SCHEMA_CATALOG

yaml = ruamel.yaml.YAML(typ="safe")
HERE = Path(__file__).parent
CONFIG_FILE = HERE.parent.parent / ".pre-commit-hooks.yaml"


def test_schema_catalog_is_alphabetized():
    catalog_keys = list(SCHEMA_CATALOG.keys())
    sorted_keys = sorted(catalog_keys)
    assert catalog_keys == sorted_keys


def test_hooks_cover_catalog():
    with open(CONFIG_FILE, "rb") as fp:
        config = yaml.load(fp)
    config_hook_ids = {x["id"] for x in config}
    catalog_hook_ids = {f"check-{name}" for name in SCHEMA_CATALOG}
    assert catalog_hook_ids <= config_hook_ids


def test_github_workflows_require_timeout_hook_uses_custom_schema():
    with open(CONFIG_FILE, "rb") as fp:
        config = yaml.load(fp)

    hook = next(
        item
        for item in config
        if item["id"] == "check-github-workflows-require-timeout"
    )
    assert hook["entry"] == (
        "check-jsonschema --builtin-schema custom.github-workflows-require-timeout"
    )
    assert hook["files"] == r"^\.github/workflows/[^/]+$"
    assert hook["types"] == ["yaml"]
