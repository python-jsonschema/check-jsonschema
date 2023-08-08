import os
import pathlib

import pytest
import responses

from check_jsonschema.schema_loader import SchemaLoader, SchemaParseError
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
    f.write_text(
        """
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
"""
    )
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
    f.write_text(
        """\
a: {b
"""
    )
    sl = SchemaLoader(str(f))
    with pytest.raises(SchemaParseError):
        sl.get_schema()
