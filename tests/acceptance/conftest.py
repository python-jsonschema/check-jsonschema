import pytest
from click.testing import CliRunner

from check_jsonschema import main as cli_main


@pytest.fixture
def cli_runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def run_line(cli_runner):
    def func(cli_args, *args, **kwargs):
        assert cli_args[0] == "check-jsonschema"
        if "catch_exceptions" not in kwargs:
            kwargs["catch_exceptions"] = False
        return cli_runner.invoke(cli_main, cli_args[1:], *args, **kwargs)

    return func


@pytest.fixture
def run_line_simple(run_line):
    def func(cli_args, *args, **kwargs):
        res = run_line(["check-jsonschema"] + cli_args, *args, **kwargs)
        assert res.exit_code == 0

    return func
