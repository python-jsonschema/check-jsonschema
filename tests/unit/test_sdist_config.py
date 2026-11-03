"""
Guard the ``[tool.flit.sdist]`` manifest against silent breakage.

flit ignores entries in the include list which do not match anything, so a typo
such as ``.github/AI_POLICY.md.md`` produces a distribution which is missing the
intended file without failing the build. Validate the manifest while the sdist
sources are still available.
"""

from __future__ import annotations

import glob
import tomllib
from pathlib import Path, PurePath

import pytest

HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parent.parent

# project files which are not picked up automatically by flit and are therefore
# only shipped if the include list names them
INCLUDED_IN_SDIST = [
    ".github/AI_POLICY.md",
    ".github/CONTRIBUTING.md",
    "CHANGELOG.rst",
    # needed as a data file for the tests (several tests check integrity
    # against this file)
    ".pre-commit-hooks.yaml",
]


def get_sdist_include() -> list[str]:
    with open(PROJECT_ROOT / "pyproject.toml", "rb") as fp:
        manifest = tomllib.load(fp)
    return manifest["tool"]["flit"]["sdist"]["include"]  # type: ignore[no-any-return]


def is_covered(relpath: str, include: list[str]) -> bool:
    return any(PurePath(relpath).match(pattern) for pattern in include)


@pytest.mark.parametrize("relpath", get_sdist_include())
def test_sdist_include_entries_refer_to_existing_files(relpath: str) -> None:
    if glob.has_magic(relpath):
        pytest.skip(f"{relpath} is a glob pattern")
    assert (PROJECT_ROOT / relpath).exists(), (
        f"The sdist include list names {relpath!r}, which does not exist, so an"
        " intended file is silently left out of the distribution"
    )


@pytest.mark.parametrize("relpath", INCLUDED_IN_SDIST)
def test_project_files_are_in_sdist(relpath: str) -> None:
    assert (PROJECT_ROOT / relpath).exists(), f"{relpath} is missing from the repo"
    assert is_covered(relpath, get_sdist_include()), (
        f"{relpath} is not covered by the sdist include list, so it is left out"
        " of the distribution"
    )
