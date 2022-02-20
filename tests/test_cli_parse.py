import argparse

import pytest

from check_jsonschema.parse_cli import parse_args


class CustomArgError(ValueError):
    pass


class CustomArgParser(argparse.ArgumentParser):
    def error(self, message):
        raise CustomArgError(message)


def _call_parse(args):
    return parse_args(args, cls=CustomArgParser)


def test_requires_some_args():
    with pytest.raises(CustomArgError):
        _call_parse([])


def test_schemafile_and_instancefile():
    args = _call_parse(["--schemafile", "schema.json", "foo.json"])
    assert args.schemafile == "schema.json"
    assert list(args.instancefiles) == ["foo.json"]


def test_requires_at_least_one_instancefile():
    with pytest.raises(CustomArgError):
        _call_parse(["--schemafile", "schema.json"])


def test_requires_schemafile():
    with pytest.raises(CustomArgError):
        _call_parse(["foo.json"])


def test_no_cache_behavior():
    args = _call_parse(["--schemafile", "schema.json", "foo.json"])
    assert args.no_cache is False
    args = _call_parse(["--schemafile", "schema.json", "foo.json", "--no-cache"])
    assert args.no_cache is True


def test_mutex_schema_opts():
    with pytest.raises(CustomArgError):
        _call_parse(["--schemafile", "x.json", "--builtin-schema", "vendor.travis"])
