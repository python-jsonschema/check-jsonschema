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
    run_line_simple, tmp_path, schemaname, vendor_schemaname
):
    workflow = tmp_path / "doc.yaml"
    workflow.write_text(PASSING_WORKFLOW)

    # vendored github workflow schema passes on it
    run_line_simple(["--builtin-schema", vendor_schemaname, str(workflow)])

    run_line_simple(["--builtin-schema", schemaname, str(workflow)])


@pytest.mark.parametrize(
    "schemaname",
    ["github-workflows-require-timeout", "custom.github-workflows-require-timeout"],
)
@pytest.mark.parametrize(
    "vendor_schemaname",
    ["github-workflows", "vendor.github-workflows"],
)
def test_github_require_timeouts_failing(
    run_line, tmp_path, schemaname, vendor_schemaname
):
    workflow = tmp_path / "doc.yaml"
    workflow.write_text(FAILING_WORKFLOW)

    # vendored github workflow schema passes on it
    res1 = run_line(
        ["check-jsonschema", "--builtin-schema", vendor_schemaname, str(workflow)]
    )
    assert res1.exit_code == 0

    res2 = run_line(
        ["check-jsonschema", "--builtin-schema", schemaname, str(workflow)],
    )
    assert res2.exit_code == 1
