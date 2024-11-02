from __future__ import annotations

import dataclasses
import importlib.util
import shlex
from pathlib import Path

import pytest
import ruamel.yaml

from check_jsonschema.parsers.json5 import ENABLED as JSON5_ENABLED

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
                if example.name == "_config.yaml":
                    continue
                res[str(example.relative_to(EXAMPLE_HOOK_FILES / category))] = hookid
    return res


def _get_explicit_cases(category):
    res = []
    example_dir = EXAMPLE_EXPLICIT_FILES / category
    for example in example_dir.iterdir():
        res.append(str(example.relative_to(EXAMPLE_EXPLICIT_FILES / category)))
    return res


POSITIVE_HOOK_CASES = _build_hook_cases("positive")
NEGATIVE_HOOK_CASES = _build_hook_cases("negative")


@pytest.mark.parametrize("case_name", POSITIVE_HOOK_CASES.keys())
def test_hook_positive_examples(case_name, run_line):
    rcase = ResolvedCase.load_positive(case_name)

    hook_id = POSITIVE_HOOK_CASES[case_name]
    ret = run_line(HOOK_CONFIG[hook_id] + [rcase.path] + rcase.add_args)
    assert ret.exit_code == 0, _format_cli_result(ret, rcase)


@pytest.mark.parametrize("case_name", NEGATIVE_HOOK_CASES.keys())
def test_hook_negative_examples(case_name, run_line):
    rcase = ResolvedCase.load_negative(case_name)

    hook_id = NEGATIVE_HOOK_CASES[case_name]
    ret = run_line(HOOK_CONFIG[hook_id] + [rcase.path] + rcase.add_args)
    assert ret.exit_code == 1, _format_cli_result(ret, rcase)


@pytest.mark.parametrize("case_name", _get_explicit_cases("positive"))
def test_explicit_positive_examples(case_name, run_line):
    _check_file_format_skip(case_name)
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
    assert ret.exit_code == 0, _format_cli_result(ret)


@pytest.mark.parametrize("case_name", _get_explicit_cases("negative"))
def test_explicit_negative_examples(case_name, run_line):
    _check_file_format_skip(case_name)
    casedir = EXAMPLE_EXPLICIT_FILES / "negative" / case_name

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
    assert ret.exit_code == 1, _format_cli_result(ret)


def _check_file_format_skip(case_name):
    if case_name.endswith("json5") and not JSON5_ENABLED:
        pytest.skip("cannot check json5 support without json5 enabled")


@dataclasses.dataclass
class ResolvedCase:
    category: str
    path: str
    add_args: list[str]
    config: dict

    def check_skip(self) -> None:
        if "requires_packages" in self.config:
            for pkg in self.config["requires_packages"]:
                if _package_is_installed(pkg):
                    continue
                pytest.skip(f"cannot check because '{pkg}' is not installed")

    def __post_init__(self) -> None:
        self.check_skip()

    @classmethod
    def load_positive(cls: type[ResolvedCase], case_name: str) -> ResolvedCase:
        return cls._load("positive", case_name)

    @classmethod
    def load_negative(cls: type[ResolvedCase], case_name: str) -> ResolvedCase:
        return cls._load("negative", case_name)

    @classmethod
    def _load(cls: type[ResolvedCase], category: str, case_name: str) -> ResolvedCase:
        _check_file_format_skip(case_name)

        path = EXAMPLE_HOOK_FILES / category / case_name
        config = cls._load_file_config(path.parent / "_config.yaml", path.name)

        return cls(
            category=category,
            path=str(path),
            add_args=config.get("add_args", []),
            config=config,
        )

    @staticmethod
    def _load_file_config(config_path, name):
        if not config_path.is_file():
            return {}
        with open(config_path) as fp:
            loaded_conf = yaml.load(fp)
        files_section = loaded_conf.get("files", {})
        return files_section.get(name, {})


def _package_is_installed(pkg: str) -> bool:
    spec = importlib.util.find_spec(pkg)
    if spec is None:
        return False
    return True


def _format_cli_result(result, rcase: ResolvedCase | None = None) -> str:
    prefix = ""
    if rcase is not None:
        prefix = f"config.add_args={rcase.add_args}\n"
    return (
        f"\n{prefix}"
        f"{result.exit_code=}\n"
        f"result.stdout={result.output}\n"
        f"{result.stderr=}"
    )
