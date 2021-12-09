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


def test_github_require_timeouts_passing(cli_runner, tmp_path):
    workflow = tmp_path / "doc.yaml"
    workflow.write_text(PASSING_WORKFLOW)

    cli_runner(["--builtin-schema", "github-workflows-require-timeout", str(workflow)])


def test_github_require_timeouts_failing(cli_runner, tmp_path):
    workflow = tmp_path / "doc.yaml"
    workflow.write_text(FAILING_WORKFLOW)

    res = cli_runner(
        ["--builtin-schema", "github-workflows-require-timeout", str(workflow)],
        expect_ok=False,
    )
    assert res.exit_code == 1

    # vendored github workflow schema passes on it
    cli_runner(["--builtin-schema", "vendor.github-workflow", str(workflow)])
