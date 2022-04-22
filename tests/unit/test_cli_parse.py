import sys
from unittest import mock

import pytest
from click.testing import CliRunner

from check_jsonschema import main as cli_main
from check_jsonschema.cli import CommandState, SchemaLoadingMode


# py3.7 compatibility: mock call objects are specialized tuples
# and they may be 2-tuples or 3-tuples
# in py3.8, `kwargs` was added as an attribute
def _get_call_kwargs(mock_obj):
    call_obj = mock_obj.call_args
    if sys.version_info < (3, 8):
        if len(call_obj) == 2:
            _args, kwargs = call_obj
        else:
            _name, _args, kwargs = call_obj
        return kwargs
    return call_obj.kwargs


@pytest.fixture
def mock_command_state():
    state = CommandState()
    with mock.patch("check_jsonschema.cli.CommandState.ensure") as m:
        m.return_value = state
        yield state


@pytest.fixture(autouse=True)
def mock_cli_exec():
    with mock.patch("check_jsonschema.cli.execute") as m:
        yield m


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


@pytest.mark.parametrize(
    "schemafile,builtin_schema,check_metaschema,expect_mode",
    [
        ("foo.json", None, False, SchemaLoadingMode.filepath),
        (None, "foo", False, SchemaLoadingMode.builtin),
        (None, None, True, SchemaLoadingMode.metaschema),
    ],
)
def test_command_state_set_schema(
    schemafile, builtin_schema, check_metaschema, expect_mode
):
    state = CommandState()
    # access prior to setting raises an error
    with pytest.raises(ValueError):
        state.schema_mode
    with pytest.raises(ValueError):
        state.schema_path
    state.set_schema(schemafile, builtin_schema, check_metaschema)
    assert state.schema_mode == expect_mode
    if schemafile:
        assert state.schema_path == schemafile
    if builtin_schema:
        assert state.schema_path == builtin_schema
    if check_metaschema:
        with pytest.raises(ValueError):
            state.schema_path


def test_requires_some_args(runner):
    result = runner.invoke(cli_main, [])
    assert result.exit_code == 2


def test_schemafile_and_instancefile(runner, mock_command_state, mock_cli_exec):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_command_state.schema_mode == SchemaLoadingMode.filepath
    assert mock_command_state.schema_path == "schema.json"
    call_kwargs = _get_call_kwargs(mock_cli_exec)
    assert call_kwargs["instancefiles"] == ("foo.json",)


def test_requires_at_least_one_instancefile(runner):
    result = runner.invoke(cli_main, ["--schemafile", "schema.json"])
    assert result.exit_code == 2


def test_requires_schemafile(runner):
    result = runner.invoke(cli_main, ["foo.json"])
    assert result.exit_code == 2


def test_no_cache_defaults_false(runner, mock_cli_exec):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    call_kwargs = _get_call_kwargs(mock_cli_exec)
    assert call_kwargs["no_cache"] is False


def test_no_cache_flag_is_true(runner, mock_cli_exec):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json", "--no-cache"])
    call_kwargs = _get_call_kwargs(mock_cli_exec)
    assert call_kwargs["no_cache"] is True


@pytest.mark.parametrize(
    "cmd_args",
    [
        [
            "--schemafile",
            "x.json",
            "--builtin-schema",
            "vendor.travis",
            "foo.json",
        ],
        [
            "--schemafile",
            "x.json",
            "--builtin-schema",
            "vendor.travis",
            "--check-metaschema",
            "foo.json",
        ],
        [
            "--schemafile",
            "x.json",
            "--check-metaschema",
            "foo.json",
        ],
        [
            "--builtin-schema",
            "vendor.travis",
            "--check-metaschema",
            "foo.json",
        ],
    ],
)
def test_mutex_schema_opts(runner, cmd_args):
    result = runner.invoke(cli_main, cmd_args)
    assert result.exit_code == 2
    assert "are mutually exclusive" in result.stderr
