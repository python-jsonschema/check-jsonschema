from __future__ import annotations

from unittest import mock

import click
import pytest

from check_jsonschema import main as cli_main
from check_jsonschema.cli.parse_result import ParseResult, SchemaLoadingMode


class BoxedContext:
    ref = None


def touch_files(dirpath, *filenames):
    for fname in filenames:
        (dirpath / fname).touch()


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


def test_requires_some_args(cli_runner):
    result = cli_runner.invoke(cli_main, [])
    assert result.exit_code == 2


def test_schemafile_and_instancefile(
    cli_runner, mock_parse_result, in_tmp_dir, tmp_path
):
    touch_files(tmp_path, "foo.json")
    cli_runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_parse_result.schema_mode == SchemaLoadingMode.filepath
    assert mock_parse_result.schema_path == "schema.json"
    assert isinstance(mock_parse_result.instancefiles, tuple)
    for f in mock_parse_result.instancefiles:
        assert isinstance(f, click.utils.LazyFile)
    assert tuple(f.name for f in mock_parse_result.instancefiles) == ("foo.json",)


def test_requires_at_least_one_instancefile(cli_runner):
    result = cli_runner.invoke(cli_main, ["--schemafile", "schema.json"])
    assert result.exit_code == 2


def test_requires_schemafile(cli_runner, in_tmp_dir, tmp_path):
    touch_files(tmp_path, "foo.json")
    result = cli_runner.invoke(cli_main, ["foo.json"])
    assert result.exit_code == 2


def test_no_cache_defaults_false(cli_runner, mock_parse_result):
    cli_runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert mock_parse_result.disable_cache is False


def test_no_cache_flag_is_true(cli_runner, mock_parse_result, in_tmp_dir, tmp_path):
    touch_files(tmp_path, "foo.json")
    cli_runner.invoke(
        cli_main, ["--schemafile", "schema.json", "foo.json", "--no-cache"]
    )
    assert mock_parse_result.disable_cache is True


@pytest.mark.parametrize(
    "cmd_args",
    [
        [
            "--schemafile",
            "x.json",
            "--builtin-schema",
            "vendor.travis",
        ],
        [
            "--schemafile",
            "x.json",
            "--builtin-schema",
            "vendor.travis",
            "--check-metaschema",
        ],
        [
            "--schemafile",
            "x.json",
            "--check-metaschema",
        ],
        [
            "--builtin-schema",
            "vendor.travis",
            "--check-metaschema",
        ],
    ],
)
def test_mutex_schema_opts(cli_runner, cmd_args, in_tmp_dir, tmp_path):
    touch_files(tmp_path, "foo.json")
    result = cli_runner.invoke(cli_main, cmd_args + ["foo.json"])
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
def test_supports_common_option(cli_runner, cmd_args):
    result = cli_runner.invoke(cli_main, cmd_args)
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "setting,expect_value", [(None, None), ("1", False), ("0", False)]
)
def test_no_color_env_var(
    cli_runner, monkeypatch, setting, expect_value, boxed_context, in_tmp_dir, tmp_path
):
    if setting is None:
        monkeypatch.delenv("NO_COLOR", raising=False)
    else:
        monkeypatch.setenv("NO_COLOR", setting)

    touch_files(tmp_path, "foo.json")
    cli_runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
    assert boxed_context.ref.color == expect_value


@pytest.mark.parametrize(
    "setting,expected_value",
    [(None, None), ("auto", None), ("always", True), ("never", False)],
)
def test_color_cli_option(
    cli_runner, setting, expected_value, boxed_context, in_tmp_dir, tmp_path
):
    args = ["--schemafile", "schema.json", "foo.json"]
    if setting:
        args.extend(("--color", setting))
    touch_files(tmp_path, "foo.json")
    cli_runner.invoke(cli_main, args)
    assert boxed_context.ref.color == expected_value


def test_no_color_env_var_overrides_cli_option(
    cli_runner, monkeypatch, mock_cli_exec, boxed_context, in_tmp_dir, tmp_path
):
    monkeypatch.setenv("NO_COLOR", "1")
    touch_files(tmp_path, "foo.json")
    cli_runner.invoke(
        cli_main, ["--color=always", "--schemafile", "schema.json", "foo.json"]
    )
    assert boxed_context.ref.color is False


@pytest.mark.parametrize(
    "setting,expected_value",
    [("auto", 0), ("always", 0), ("never", 0), ("anything_else", 2)],
)
def test_color_cli_option_is_choice(
    cli_runner, setting, expected_value, in_tmp_dir, tmp_path
):
    touch_files(tmp_path, "foo.json")
    assert (
        cli_runner.invoke(
            cli_main,
            ["--color", setting, "--schemafile", "schema.json", "foo.json"],
        ).exit_code
        == expected_value
    )


def test_formats_default_to_enabled(
    cli_runner, mock_parse_result, in_tmp_dir, tmp_path
):
    touch_files(tmp_path, "foo.json")
    cli_runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
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
def test_disable_selected_formats(
    cli_runner, mock_parse_result, addargs, in_tmp_dir, tmp_path
):
    touch_files(tmp_path, "foo.json")
    cli_runner.invoke(
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
def test_disable_all_formats(
    cli_runner, mock_parse_result, addargs, in_tmp_dir, tmp_path
):
    touch_files(tmp_path, "foo.json")
    # this should be an override, with or without other args
    cli_runner.invoke(
        cli_main,
        [
            "--schemafile",
            "schema.json",
            "foo.json",
        ]
        + addargs,
    )
    assert mock_parse_result.disable_all_formats is True


def test_can_specify_custom_validator_class(
    cli_runner, mock_parse_result, mock_module, in_tmp_dir, tmp_path
):
    mock_module("foo.py", "class MyValidator: pass")
    import foo

    touch_files(tmp_path, "foo.json")
    result = cli_runner.invoke(
        cli_main,
        [
            "--schemafile",
            "schema.json",
            "foo.json",
            "--validator-class",
            "foo:MyValidator",
        ],
    )
    assert result.exit_code == 0
    assert mock_parse_result.validator_class == foo.MyValidator


@pytest.mark.parametrize(
    "failmode", ("syntax", "import", "attr", "function", "non_callable")
)
def test_custom_validator_class_fails(
    cli_runner, mock_parse_result, mock_module, failmode, in_tmp_dir, tmp_path
):
    mock_module(
        "foo.py",
        """\
class MyValidator: pass

def validator_func(*args, **kwargs):
    return MyValidator(*args, **kwargs)

other_thing = 100
""",
    )

    if failmode == "syntax":
        arg = "foo.MyValidator"
    elif failmode == "import":
        arg = "foo.bar:MyValidator"
    elif failmode == "attr":
        arg = "foo:no_such_attr"
    elif failmode == "function":
        arg = "foo:validator_func"
    elif failmode == "non_callable":
        arg = "foo:other_thing"
    else:
        raise NotImplementedError

    touch_files(tmp_path, "foo.json")
    result = cli_runner.invoke(
        cli_main,
        ["--schemafile", "schema.json", "foo.json", "--validator-class", arg],
    )
    assert result.exit_code == 2

    if failmode == "syntax":
        assert "is not a valid specifier" in result.stderr
    elif failmode == "import":
        assert "was not an importable module" in result.stderr
    elif failmode == "attr":
        assert "was not resolvable to a class" in result.stderr
    elif failmode in ("function", "non_callable"):
        assert "is not a class" in result.stderr
    else:
        raise NotImplementedError
