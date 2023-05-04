from __future__ import annotations

from unittest import mock

import click
import pytest
from click.testing import CliRunner

from check_jsonschema import main as cli_main
from check_jsonschema.cli.parse_result import ParseResult, SchemaLoadingMode


class BoxedContext:
    ref = None


@pytest.fixture
def boxed_context():
    return BoxedContext()


@pytest.fixture
def mock_parse_result():
    args = ParseResult()
    with mock.patch("check_jsonschema.cli.main_command.ParseResult") as m:
        m.return_value = args
        yield args


@pytest.fixture(autouse=True)
def mock_cli_exec(boxed_context):
    def get_ctx(*args):
        boxed_context.ref = click.get_current_context()

    with mock.patch(
        "check_jsonschema.cli.main_command.execute", side_effect=get_ctx
    ) as m:
        yield m


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


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


def test_requires_some_args(runner):
    result = runner.invoke(cli_main, [])
    assert result.exit_code == 2


def test_schemafile_and_instancefile(runner, mock_parse_result):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_parse_result.schema_mode == SchemaLoadingMode.filepath
    assert mock_parse_result.schema_path == "schema.json"
    assert mock_parse_result.instancefiles == ("foo.json",)


def test_requires_at_least_one_instancefile(runner):
    result = runner.invoke(cli_main, ["--schemafile", "schema.json"])
    assert result.exit_code == 2


def test_requires_schemafile(runner):
    result = runner.invoke(cli_main, ["foo.json"])
    assert result.exit_code == 2


def test_no_cache_defaults_false(runner, mock_parse_result):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_parse_result.disable_cache is False


def test_no_cache_flag_is_true(runner, mock_parse_result):
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
def test_mutex_schema_opts(runner, cmd_args):
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
def test_supports_common_option(runner, cmd_args):
    result = runner.invoke(cli_main, cmd_args)
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "setting,expect_value", [(None, None), ("1", False), ("0", False)]
)
def test_no_color_env_var(runner, monkeypatch, setting, expect_value, boxed_context):
    if setting is None:
        monkeypatch.delenv("NO_COLOR", raising=False)
    else:
        monkeypatch.setenv("NO_COLOR", setting)

    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert boxed_context.ref.color == expect_value


@pytest.mark.parametrize(
    "setting,expected_value",
    [(None, None), ("auto", None), ("always", True), ("never", False)],
)
def test_color_cli_option(runner, setting, expected_value, boxed_context):
    args = ["--schemafile", "schema.json", "foo.json"]
    if setting:
        args.extend(("--color", setting))
    runner.invoke(cli_main, args)
    assert boxed_context.ref.color == expected_value


def test_no_color_env_var_overrides_cli_option(
    runner, monkeypatch, mock_cli_exec, boxed_context
):
    monkeypatch.setenv("NO_COLOR", "1")
    runner.invoke(
        cli_main, ["--color=always", "--schemafile", "schema.json", "foo.json"]
    )
    assert boxed_context.ref.color is False


@pytest.mark.parametrize(
    "setting,expected_value",
    [("auto", 0), ("always", 0), ("never", 0), ("anything_else", 2)],
)
def test_color_cli_option_is_choice(runner, setting, expected_value):
    assert (
        runner.invoke(
            cli_main, ["--color", setting, "--schemafile", "schema.json", "foo.json"]
        ).exit_code
        == expected_value
    )


def test_formats_default_to_enabled(runner, mock_parse_result):
    runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_parse_result.disable_all_formats is False
    assert mock_parse_result.disable_formats == ()


@pytest.mark.parametrize(
    "addargs",
    (
        [
            "--disable-formats",
            "uri-reference",
            "--disable-formats",
            "date-time",
        ],
        ["--disable-formats", "uri-reference,date-time"],
    ),
)
def test_disable_selected_formats(runner, mock_parse_result, addargs):
    runner.invoke(
        cli_main,
        [
            "--schemafile",
            "schema.json",
            "foo.json",
        ]
        + addargs,
    )
    assert mock_parse_result.disable_all_formats is False
    assert set(mock_parse_result.disable_formats) == {"uri-reference", "date-time"}


@pytest.mark.parametrize(
    "addargs",
    (
        [
            "--disable-formats",
            "uri-reference",
            "--disable-formats",
            "date-time",
            "--disable-formats",
            "*",
        ],
        ["--disable-formats", "*"],
        ["--disable-formats", "*,email"],
    ),
)
def test_disable_all_formats(runner, mock_parse_result, addargs):
    # this should be an override, with or without other args
    runner.invoke(
        cli_main,
        [
            "--schemafile",
            "schema.json",
            "foo.json",
        ]
        + addargs,
    )
    assert mock_parse_result.disable_all_formats is True


def test_disable_format_deprecated_flag(runner, mock_parse_result):
    # this should be an override, with or without other args
    with pytest.warns(UserWarning, match="'--disable-format' is deprecated"):
        runner.invoke(
            cli_main, ["--schemafile", "schema.json", "foo.json", "--disable-format"]
        )
    assert mock_parse_result.disable_all_formats is True
