import shlex
from pathlib import Path

import pytest
import ruamel.yaml

from check_jsonschema.parsers.json5 import ENABLED as JSON5_ENABLED
from check_jsonschema.parsers.toml import ENABLED as TOML_ENABLED

yaml = ruamel.yaml.YAML(typ="safe")

HERE = Path(__file__).parent
EXAMPLE_FILES = HERE.parent / "example-files"
EXAMPLE_HOOK_FILES = HERE.parent / "example-files" / "hooks"
EXAMPLE_EXPLICIT_FILES = HERE.parent / "example-files" / "explicit-schema"


def _iter_hook_config():
    config_file = HERE.parent.parent / ".pre-commit-hooks.yaml"
    with open(config_file) as fp:
        for hook in yaml.load(fp):
            hookid = hook["id"]
            if not hookid.startswith("check-"):
                continue
            hookid = hookid[len("check-") :]
            entry = shlex.split(hook["entry"])
            yield (hookid, entry)


HOOK_CONFIG = dict(_iter_hook_config())


def _build_hook_cases(category):
    res = {}
    for hookid in HOOK_CONFIG:
        example_dir = EXAMPLE_HOOK_FILES / category / hookid
        if example_dir.exists():
            for example in example_dir.iterdir():
                res[str(example.relative_to(EXAMPLE_HOOK_FILES / category))] = hookid
    return res


def _get_explicit_cases(category):
    res = []
    example_dir = EXAMPLE_EXPLICIT_FILES / category
    for example in example_dir.iterdir():
        res.append(str(example.relative_to(EXAMPLE_EXPLICIT_FILES / category)))
    return res


def _check_case_skip(case_name):
    if case_name.endswith("json5") and not JSON5_ENABLED:
        pytest.skip("cannot check json5 support without json5 enabled")
    if case_name.endswith("toml") and not TOML_ENABLED:
        pytest.skip("cannot check toml support without toml enabled")


POSITIVE_HOOK_CASES = _build_hook_cases("positive")
NEGATIVE_HOOK_CASES = _build_hook_cases("negative")


@pytest.mark.parametrize("case_name", POSITIVE_HOOK_CASES.keys())
def test_hook_positive_examples(case_name, run_line):
    _check_case_skip(case_name)

    hook_id = POSITIVE_HOOK_CASES[case_name]
    ret = run_line(
        HOOK_CONFIG[hook_id] + [str(EXAMPLE_HOOK_FILES / "positive" / case_name)]
    )
    assert ret.exit_code == 0


@pytest.mark.parametrize("case_name", NEGATIVE_HOOK_CASES.keys())
def test_hook_negative_examples(case_name, run_line):
    _check_case_skip(case_name)
    hook_id = NEGATIVE_HOOK_CASES[case_name]
    ret = run_line(
        HOOK_CONFIG[hook_id] + [str(EXAMPLE_HOOK_FILES / "negative" / case_name)]
    )
    assert ret.exit_code == 1


@pytest.mark.parametrize("case_name", _get_explicit_cases("positive"))
def test_explicit_positive_examples(case_name, run_line):
    _check_case_skip(case_name)
    casedir = EXAMPLE_EXPLICIT_FILES / "positive" / case_name

    instance = casedir / "instance.json"
    if not instance.exists():
        instance = casedir / "instance.yaml"
    if not instance.exists():
        instance = casedir / "instance.toml"
    if not instance.exists():
        raise Exception("could not find an instance file for test case")

    schema = casedir / "schema.json"
    if not schema.exists():
        schema = casedir / "schema.yaml"
    if not schema.exists():
        raise Exception("could not find a schema file for test case")

    ret = run_line(
        [
            "check-jsonschema",
            "--schemafile",
            str(schema),
            str(instance),
        ]
    )
    assert ret.exit_code == 0
