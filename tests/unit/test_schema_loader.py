import os
import pathlib

import pytest

from check_jsonschema.schema_loader import SchemaLoader
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
    ],
)
def test_schemaloader_local_yaml_data(tmp_path, filename):
    f = tmp_path / filename
    f.write_text(
        """
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
