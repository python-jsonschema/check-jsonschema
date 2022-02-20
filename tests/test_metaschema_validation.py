from pathlib import Path

import pytest
import ruamel.yaml

from check_jsonschema import main

yaml = ruamel.yaml.YAML(typ="safe")

HERE = Path(__file__).parent
EXAMPLE_FILES = HERE / "example-files" / "metaschemas"


def _build_cases(category):
    example_dir = EXAMPLE_FILES / category
    res = []
    if example_dir.exists():
        for example in example_dir.iterdir():
            res.append(str(example.relative_to(EXAMPLE_FILES)))
    return res


POSITIVE_CASES = _build_cases("positive")
NEGATIVE_CASES = _build_cases("negative")


def run(target):
    return main(["--check-metaschema", str(target)], exit=False)


@pytest.mark.parametrize("case_name", POSITIVE_CASES)
def test_metaschema_positive_examples(case_name):
    ret = run(EXAMPLE_FILES / case_name)
    assert ret == 0


@pytest.mark.parametrize("case_name", NEGATIVE_CASES)
def test_metaschema_negative_examples(case_name):
    ret = run(EXAMPLE_FILES / case_name)
    assert ret == 1
