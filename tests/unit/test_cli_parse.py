import sys
from unittest import mock

import pytest
from click.testing import CliRunner

from check_jsonschema import main as cli_main


# py3.7 compatibility: mock call objects are specialized tuples
# and they may be 2-tuples or 3-tuples
# in py3.8, `kwargs` was added as an attribute
def _get_call_kwargs(call_obj):
    if sys.version_info < (3, 8):
        if len(call_obj) == 2:
            _args, kwargs = call_obj
        else:
            _name, _args, kwargs = call_obj
        return kwargs
    return call_obj.kwargs


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


def test_requires_some_args(runner):
    result = runner.invoke(cli_main, [])
    assert result.exit_code == 2


def test_schemafile_and_instancefile(runner):
    with mock.patch("check_jsonschema.do_main") as m:
        runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
        call_kwargs = _get_call_kwargs(m.call_args)
        assert call_kwargs["schemafile"] == "schema.json"
        assert call_kwargs["instancefiles"] == ("foo.json",)


def test_requires_at_least_one_instancefile(runner):
    result = runner.invoke(cli_main, ["--schemafile", "schema.json"])
    assert result.exit_code == 2


def test_requires_schemafile(runner):
    result = runner.invoke(cli_main, ["foo.json"])
    assert result.exit_code == 2


def test_no_cache_behavior(runner):
    with mock.patch("check_jsonschema.do_main") as m:
        runner.invoke(cli_main, ["--schemafile", "schema.json", "foo.json"])
        call_kwargs = _get_call_kwargs(m.call_args)
        assert call_kwargs["no_cache"] is False

    with mock.patch("check_jsonschema.do_main") as m:
        runner.invoke(
            cli_main, ["--schemafile", "schema.json", "foo.json", "--no-cache"]
        )
        call_kwargs = _get_call_kwargs(m.call_args)
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
