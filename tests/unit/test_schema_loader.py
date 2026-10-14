import json
import os
import pathlib

import pytest
import responses

from check_jsonschema import builtin_schemas
from check_jsonschema.formats import FormatOptions
from check_jsonschema.regex_variants import RegexImplementation, RegexVariantName
from check_jsonschema.schema_loader import (
    BuiltinSchemaLoader,
    SchemaLoader,
    SchemaParseError,
)
from check_jsonschema.schema_loader.readers import HttpSchemaReader, LocalSchemaReader


@pytest.fixture
def in_tmp_dir(request, tmp_path):
    os.chdir(str(tmp_path))
    yield
    os.chdir(request.config.invocation_dir)


@pytest.mark.parametrize(
    "filename",
    [
        "schema.json",
        "schema.yaml",
    ],
)
def test_schemaloader_path_handling_relative_local_path(in_tmp_dir, filename):
    # ensure that the file exists so that the behavior of pathlib resolution will be
    # correct on Windows with older python versions
    # see: https://bugs.python.org/issue38671
    path = pathlib.Path("path", "to") / filename
    path.parent.mkdir(parents=True)
    path.touch()

    sl = SchemaLoader(str(path))
    assert isinstance(sl.reader, LocalSchemaReader)
    assert sl.reader.filename == os.path.abspath(str(path))
    assert str(sl.reader.path) == str(path.resolve())


@pytest.mark.parametrize(
    "filename",
    [
        "schema.yaml",
        "schema.yml",
        "https://foo.example.com/schema.yaml",
        "https://foo.example.com/schema.yml",
    ],
)
def test_schemaloader_yaml_data(tmp_path, filename):
    schema_text = """
---
"$schema": https://json-schema.org/draft/2020-12/schema
type: object
properties:
  a:
    type: object
    properties:
      b:
        type: array
        items:
          type: integer
      c:
        type: string
"""
    if filename.startswith("http"):
        responses.add("GET", filename, body=schema_text)
        path = filename
    else:
        f = tmp_path / filename
        f.write_text(schema_text)
        path = str(f)
    sl = SchemaLoader(path)
    schema = sl.get_schema()
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "a": {
                "type": "object",
                "properties": {
                    "b": {"type": "array", "items": {"type": "integer"}},
                    "c": {"type": "string"},
                },
            },
        },
    }


@pytest.mark.parametrize(
    "schemafile",
    [
        "https://foo.example.com/schema.json",
        "http://foo.example.com/schema.json",
    ],
)
def test_schemaloader_remote_path(schemafile):
    sl = SchemaLoader(schemafile)
    assert isinstance(sl.reader, HttpSchemaReader)
    assert sl.reader.url == schemafile


def test_schemaloader_local_yaml_dup_anchor(tmp_path):
    f = tmp_path / "schema.yaml"
    f.write_text("""
---
"$schema": https://json-schema.org/draft/2020-12/schema
type: object
properties:
  a:
    type: object
    properties:
      b: &anchor
        type: array
        items:
          type: integer
      c: &anchor
        type: string
""")
    sl = SchemaLoader(str(f))
    schema = sl.get_schema()
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "a": {
                "type": "object",
                "properties": {
                    "b": {"type": "array", "items": {"type": "integer"}},
                    "c": {"type": "string"},
                },
            },
        },
    }


def test_schemaloader_invalid_yaml_data(tmp_path):
    f = tmp_path / "foo.yaml"
    f.write_text("""\
a: {b
""")
    sl = SchemaLoader(str(f))
    with pytest.raises(SchemaParseError):
        sl.get_schema()


def _validator_for(loader):
    regex_impl = RegexImplementation(RegexVariantName.default)
    return loader.get_validator(
        "instance.json",
        {},
        FormatOptions(regex_impl=regex_impl, enabled=False),
        regex_impl,
        False,
    )


@pytest.mark.parametrize("schema_name", ["github-workflows", "vendor.github-workflows"])
@pytest.mark.parametrize(
    "base_uri",
    [
        "https://json.schemastore.org/base.json",
        "https://www.schemastore.org/base.json",
    ],
)
def test_vendored_schema_resolves_schemastore_base_offline(
    monkeypatch, schema_name, base_uri
):
    get_vendored_schema = builtin_schemas._get_vendored_schema

    def get_schema(name):
        if name == "github-workflows":
            return {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "$ref": f"{base_uri}#/definitions/timezone",
            }
        return get_vendored_schema(name)

    monkeypatch.setattr(builtin_schemas, "_get_vendored_schema", get_schema)
    validator = _validator_for(BuiltinSchemaLoader(schema_name))

    assert validator.is_valid("Europe/London")
    assert not validator.is_valid("Mars/Olympus_Mons")
    assert not responses.calls


@pytest.mark.parametrize(
    "schema_name",
    [
        None,
        "github-workflows-require-timeout",
        "custom.github-workflows-require-timeout",
    ],
)
def test_other_schemas_retrieve_schemastore_base(tmp_path, monkeypatch, schema_name):
    base_uri = "https://json.schemastore.org/base.json"
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$ref": f"{base_uri}#/definitions/timezone",
    }
    responses.add(
        "GET", base_uri, json={"definitions": {"timezone": {"const": "remote"}}}
    )
    if schema_name is None:
        path = tmp_path / "schema.json"
        path.write_text(json.dumps(schema))
        loader = SchemaLoader(str(path))
    else:
        monkeypatch.setattr(builtin_schemas, "_get_custom_schema", lambda name: schema)
        loader = BuiltinSchemaLoader(schema_name)
    validator = _validator_for(loader)

    assert validator.is_valid("remote")
    assert not validator.is_valid("Europe/London")
    assert len(responses.calls) == 1


@pytest.mark.parametrize(
    "base_uri",
    [
        "https://json.schemastore.org/base.json",
        "https://www.schemastore.org/base.json",
    ],
)
def test_vendored_reference_does_not_replace_root_schema(monkeypatch, base_uri):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": {"timezone": {"const": "root"}},
        "$ref": "#/definitions/timezone",
    }
    get_vendored_schema = builtin_schemas._get_vendored_schema

    def get_schema(name):
        if name == "github-workflows":
            return schema.copy()
        return get_vendored_schema(name)

    monkeypatch.setattr(builtin_schemas, "_get_vendored_schema", get_schema)
    loader = BuiltinSchemaLoader("vendor.github-workflows", base_uri=base_uri)
    validator = _validator_for(loader)

    assert validator.is_valid("root")
    assert not validator.is_valid("Europe/London")
    assert not responses.calls
