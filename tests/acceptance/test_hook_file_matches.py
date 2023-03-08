from __future__ import annotations

import pathlib
import re

import pytest
import ruamel.yaml

yaml = ruamel.yaml.YAML(typ="safe")

HERE = pathlib.Path(__file__).parent


def check_pattern_match(
    pattern: str | re.Pattern, value: str, *, should_match: bool = True
) -> None:
    __tracebackhide__ = True
    if not isinstance(pattern, re.Pattern):
        pattern = re.compile(pattern)

    matches = bool(pattern.fullmatch(value))

    if matches == should_match:
        return

    if should_match:
        pytest.fail(f"'{pattern}' did not match '{value}' (expected match)")
    else:
        pytest.fail(f"'{pattern}' matched '{value}' (expected no match)")


def get_hook_config(hookid):
    config_file = HERE.parent.parent / ".pre-commit-hooks.yaml"
    with open(config_file) as fp:
        for hook in yaml.load(fp):
            if hook["id"] == hookid:
                return hook
        else:
            raise LookupError(f"could not find hook with id={hookid}")


_HOOKID_PATH_MAP = {
    "check-azure-pipelines": {
        "good": (
            "azure-pipelines.yml",
            "azure-pipelines.yaml",
            ".azure-pipelines.yml",
            ".azure-pipelines.yaml",
        ),
        "bad": (
            "foo.yml",
            "foo/azure-pipelines.yaml",
        ),
    },
    "check-bamboo-spec": {
        "good": (
            "bamboo-specs/foo.yml",
            "bamboo-specs/foo.yaml",
        ),
        "bad": (
            "bamboo-specs.yaml",
            "bamboo-spec/foo.yml",
            "bamboo-specs/README.md",
        ),
    },
    "check-dependabot": {
        "good": (".github/dependabot.yml", ".github/dependabot.yaml"),
        "bad": (".dependabot.yaml", ".dependabot.yml"),
    },
    "check-github-actions": {
        "good": (
            "action.yaml",
            ".github/actions/action.yml",
            ".github/actions/foo/bar/action.yaml",
            ".github/actions/path with spaces/action.yml",
        ),
        "bad": (".github/actions/foo/other.yaml",),
    },
    "check-github-workflows": {
        "good": (
            ".github/workflows/build.yml",
            ".github/workflows/build.yaml",
        ),
        "bad": (
            ".github/workflows.yaml",
            ".github/workflows/foo/bar.yaml",
        ),
    },
    "check-gitlab-ci": {
        "good": (
            ".gitlab-ci.yml",
            ".gitlab/.gitlab-ci.yml",
            "gitlab/.gitlab-ci.yml",
        ),
        "bad": (
            ".gitlab-ci.yaml",
            "gitlab-ci.yml",
            ".gitlab/gitlab-ci.yml",
            "gitlab/gitlab-ci.yml",
        ),
    },
    "check-readthedocs": {
        "good": (
            ".readthedocs.yml",
            ".readthedocs.yaml",
        ),
        "bad": (
            "readthedocs.yml",
            "readthedocs.yaml",
        ),
    },
    "check-renovate": {
        "good": (
            "renovate.json",
            "renovate.json5",
            ".github/renovate.json",
            ".gitlab/renovate.json5",
            ".renovaterc",
            ".renovaterc.json",
        ),
        "bad": (
            ".github/renovaterc",
            ".renovate",
            ".renovate.json",
        ),
    },
    "check-travis": {
        "good": (
            ".travis.yml",
            ".travis.yaml",
        ),
        "bad": (
            "travis.yml",
            ".travis",
        ),
    },
}


@pytest.mark.parametrize(
    "hookid, filepath",
    [
        (hookid, path)
        for (hookid, pathlist) in _HOOKID_PATH_MAP.items()
        for path in pathlist.get("good", ())
    ],
)
def test_hook_matches_known_good_paths(hookid, filepath):
    config = get_hook_config(hookid)
    check_pattern_match(config["files"], filepath)


@pytest.mark.parametrize(
    "hookid, filepath",
    [
        (hookid, path)
        for (hookid, pathlist) in _HOOKID_PATH_MAP.items()
        for path in pathlist.get("bad", ())
    ],
)
def test_hook_does_not_matches_known_bad_paths(hookid, filepath):
    config = get_hook_config(hookid)
    check_pattern_match(config["files"], filepath, should_match=False)
