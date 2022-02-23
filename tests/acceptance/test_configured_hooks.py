import shlex
from pathlib import Path

import pytest
import ruamel.yaml

from check_jsonschema import main
from check_jsonschema.loaders.instance.json5 import ENABLED as JSON5_ENABLED

yaml = ruamel.yaml.YAML(typ="safe")

HERE = Path(__file__).parent
EXAMPLE_FILES = HERE.parent / "example-files" / "hooks"


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


def _build_cases(category):
    res = {}
    for hookid in HOOK_CONFIG:
        example_dir = EXAMPLE_FILES / category / hookid
        if example_dir.exists():
            for example in example_dir.iterdir():
                res[str(example.relative_to(EXAMPLE_FILES))] = hookid
    return res


POSITIVE_CASES = _build_cases("positive")
NEGATIVE_CASES = _build_cases("negative")


def run(base_cmd, target):
    cmd = base_cmd[1:] + [str(target)]
    return main(cmd, exit=False)


@pytest.mark.parametrize("case_name", POSITIVE_CASES.keys())
def test_hook_positive_examples(case_name):
    if case_name.endswith("json5") and not JSON5_ENABLED:
        pytest.skip("cannot check json5 support without json5 enabled")

    hook_id = POSITIVE_CASES[case_name]
    ret = run(HOOK_CONFIG[hook_id], EXAMPLE_FILES / case_name)
    assert ret == 0


@pytest.mark.parametrize("case_name", NEGATIVE_CASES.keys())
def test_hook_negative_examples(case_name):
    hook_id = NEGATIVE_CASES[case_name]
    ret = run(HOOK_CONFIG[hook_id], EXAMPLE_FILES / case_name)
    assert ret == 1
