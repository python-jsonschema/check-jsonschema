from __future__ import annotations

import typing as t
from unittest import mock

import click
import pytest
from click.testing import CliRunner
from click.testing import Result as ClickResult

from check_jsonschema import main as cli_main
from check_jsonschema.cli import ParseResult, SchemaLoadingMode


@pytest.fixture
def mock_parse_result():
    args = ParseResult()
    with mock.patch("check_jsonschema.cli.ParseResult") as m:
        m.return_value = args
        yield args


@pytest.fixture(autouse=True)
def mock_cli_exec():
    with mock.patch("check_jsonschema.cli.execute") as m:
        yield m


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def invoke_and_get_ctx(
    runner: CliRunner,
    cmd: click.Command,
    args: t.Sequence[str],
) -> tuple[ClickResult, click.Context]:
    # There doesn't appear to be a good way to get the Click context used by a
    # test invocation, so we replace the invoke method with a wrapper that
    # calls `click.get_current_context` to extract the context object.

    ctx = None

    def extract_ctx(*args, **kwargs):
        nonlocal ctx
        ctx = click.get_current_context()
        return click.Command.invoke(*args, **kwargs)

    with mock.patch("click.Command.invoke", extract_ctx):
        results = runner.invoke(cmd, args)

    return results, ctx


@pytest.mark.parametrize(
    "schemafile,builtin_schema,check_metaschema,expect_mode",
    [
        ("foo.json", None, False, SchemaLoadingMode.filepath),
        (None, "foo", False, SchemaLoadingMode.builtin),
        (None, None, True, SchemaLoadingMode.metaschema),
    ],
)
def test_parse_result_set_schema(
    schemafile, builtin_schema, check_metaschema, expect_mode
):
    args = ParseResult()
    # starts as None (always)
    assert args.schema_path is None

    args.set_schema(schemafile, builtin_schema, check_metaschema)
    assert args.schema_mode == expect_mode
    if schemafile:
        assert args.schema_path == schemafile
    if builtin_schema:
        assert args.schema_path == builtin_schema
    if check_metaschema:
        assert args.schema_path is None


def test_requires_some_args(runner: CliRunner):
    result = runner.invoke(cli_main, [])
    assert result.exit_code == 2


def test_schemafile_and_instancefile(runner: CliRunner, mock_parse_result: ParseResult):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_parse_result.schema_mode == SchemaLoadingMode.filepath
    assert mock_parse_result.schema_path == "schema.json"
    assert mock_parse_result.instancefiles == ("foo.json",)


def test_requires_at_least_one_instancefile(runner: CliRunner):
    result = runner.invoke(cli_main, ["--schemafile", "schema.json"])
    assert result.exit_code == 2


def test_requires_schemafile(runner: CliRunner):
    result = runner.invoke(cli_main, ["foo.json"])
    assert result.exit_code == 2


def test_no_cache_defaults_false(runner: CliRunner, mock_parse_result: ParseResult):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_parse_result.disable_cache is False


def test_no_cache_flag_is_true(runner: CliRunner, mock_parse_result: ParseResult):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json", "--no-cache"])
    assert mock_parse_result.disable_cache is True


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
def test_mutex_schema_opts(runner: CliRunner, cmd_args: list[str]):
    result = runner.invoke(cli_main, cmd_args)
    assert result.exit_code == 2
    assert "are mutually exclusive" in result.stderr


@pytest.mark.parametrize(
    "cmd_args",
    [
        ["--version"],
        ["--help"],
        ["-h"],
    ],
)
def test_supports_common_option(runner: CliRunner, cmd_args: list[str]):
    result = runner.invoke(cli_main, cmd_args)
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "setting,expect_value", [(None, None), ("1", False), ("0", False)]
)
def test_no_color_env_var(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    setting: str | None,
    expect_value: bool | None,
):
    if setting is None:
        monkeypatch.delenv("NO_COLOR", raising=False)
    else:
        monkeypatch.setenv("NO_COLOR", setting)

    _, ctx = invoke_and_get_ctx(
        runner, cli_main, ["--schemafile", "schema.json", "foo.json"]
    )
    assert ctx.color == expect_value


@pytest.mark.parametrize(
    "setting,expected_value",
    [(None, None), ("auto", None), ("always", True), ("never", False)],
)
def test_color_cli_option(
    runner: CliRunner,
    setting: str | None,
    expected_value: bool | None,
):
    args = ["--schemafile", "schema.json", "foo.json"]
    if setting:
        args.extend(("--color", setting))
    _, ctx = invoke_and_get_ctx(runner, cli_main, args)
    assert ctx.color == expected_value


def test_no_color_env_var_overrides_cli_option(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("NO_COLOR", "1")

    _, ctx = invoke_and_get_ctx(
        runner, cli_main, ["--color=always", "--schemafile", "schema.json", "foo.json"]
    )
    assert ctx.color is False


@pytest.mark.parametrize(
    "setting,expected_value",
    [("auto", 0), ("always", 0), ("never", 0), ("anything_else", 2)],
)
def test_color_cli_option_is_choice(
    runner: CliRunner, setting: str, expected_value: int
):
    assert (
        runner.invoke(
            cli_main, ["--color", setting, "--schemafile", "schema.json", "foo.json"]
        ).exit_code
        == expected_value
    )
