import click
import pytest

from check_jsonschema.cli.warnings import deprecation_warning_callback


@click.command("foo")
@click.option(
    "--bar",
    is_flag=True,
    callback=deprecation_warning_callback("--bar", is_flag=True),
)
@click.option(
    "--baz",
    callback=deprecation_warning_callback(
        "--baz", append_message="Use --frob instead!"
    ),
)
def mycli(bar, baz):
    print(bar)
    if baz:
        print(baz)


def test_deprecation_warning_callback_on_missing_opts(cli_runner):
    result = cli_runner.invoke(mycli, [])
    assert result.exit_code == 0
    assert result.stdout == "False\n"


def test_deprecation_warning_callback_on_flag(cli_runner):
    with pytest.warns(
        UserWarning,
        match="'--bar' is deprecated and will be removed in a future release",
    ):
        result = cli_runner.invoke(mycli, ["--bar"], catch_exceptions=False)
    assert result.exit_code == 0, result.stdout
    assert result.stdout == "True\n"


def test_deprecation_warning_callback_added_message(cli_runner):
    with pytest.warns(
        UserWarning,
        match=(
            "'--baz' is deprecated and will be removed in a future release. "
            "Use --frob instead!"
        ),
    ):
        result = cli_runner.invoke(mycli, ["--baz", "ok"], catch_exceptions=False)
    assert result.exit_code == 0, result.stdout
    assert result.stdout == "False\nok\n"
