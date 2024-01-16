import textwrap

import pytest
from click.testing import CliRunner

from check_jsonschema.cli.commands import main_command
from check_jsonschema.cli.legacy import legacy_main


def _render_result(result):
    return f"""
output:
{textwrap.indent(result.output, "  ")}

stderr:
{textwrap.indent(result.stderr, "  ")}
"""


@pytest.fixture
def cli_runner():
    return CliRunner(mix_stderr=False)


def _get_command(legacy: bool):
    if legacy:
        return legacy_main
    else:
        return main_command


@pytest.fixture
def run_line(cli_runner):
    def func(cli_args, legacy: bool = True, *args, **kwargs):
        assert cli_args[0] == "check-jsonschema"
        if "catch_exceptions" not in kwargs:
            kwargs["catch_exceptions"] = False
        return cli_runner.invoke(_get_command(legacy), cli_args[1:], *args, **kwargs)

    return func


@pytest.fixture
def run_line_simple(run_line):
    def func(cli_args, *args, full_traceback: bool = True, **kwargs):
        res = run_line(
            ["check-jsonschema"]
            + (["--traceback-mode", "full"] if full_traceback else [])
            + cli_args,
            *args,
            **kwargs,
        )
        assert res.exit_code == 0, _render_result(res)

    return func
