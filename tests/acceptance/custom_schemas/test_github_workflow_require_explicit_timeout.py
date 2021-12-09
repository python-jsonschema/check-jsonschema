import pytest

PASSING_WORKFLOW = """\
name: build
on:
  push:
jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - name: install requirements
        run: python -m pip install tox
      - name: test
        run: python -m tox -e py
"""
FAILING_WORKFLOW = """\
name: build
on:
  push:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - name: install requirements
        run: python -m pip install tox
      - name: test
        run: python -m tox -e py
"""


@pytest.mark.parametrize(
    "schemaname",
    ["github-workflows-require-timeout", "custom.github-workflows-require-timeout"],
)
@pytest.mark.parametrize(
    "vendor_schemaname",
    ["github-workflows", "vendor.github-workflows"],
)
def test_github_require_timeouts_passing(
    cli_runner, tmp_path, schemaname, vendor_schemaname
):
    workflow = tmp_path / "doc.yaml"
    workflow.write_text(PASSING_WORKFLOW)

    # vendored github workflow schema passes on it
    cli_runner(["--builtin-schema", vendor_schemaname, str(workflow)])

    cli_runner(["--builtin-schema", schemaname, str(workflow)])


@pytest.mark.parametrize(
    "schemaname",
    ["github-workflows-require-timeout", "custom.github-workflows-require-timeout"],
)
@pytest.mark.parametrize(
    "vendor_schemaname",
    ["github-workflows", "vendor.github-workflows"],
)
def test_github_require_timeouts_failing(
    cli_runner, tmp_path, schemaname, vendor_schemaname
):
    workflow = tmp_path / "doc.yaml"
    workflow.write_text(FAILING_WORKFLOW)

    # vendored github workflow schema passes on it
    cli_runner(["--builtin-schema", vendor_schemaname, str(workflow)])

    res = cli_runner(
        ["--builtin-schema", schemaname, str(workflow)],
        expect_ok=False,
    )
    assert res.exit_code == 1
