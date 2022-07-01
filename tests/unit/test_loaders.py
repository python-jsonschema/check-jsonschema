import os
import pathlib

import pytest

from check_jsonschema.loaders import BadFileTypeError, InstanceLoader, SchemaLoader
from check_jsonschema.loaders.instance.json5 import ENABLED as JSON5_ENABLED
from check_jsonschema.loaders.instance.toml import ENABLED as TOML_ENABLED
from check_jsonschema.loaders.schema import HttpSchemaReader, LocalSchemaReader


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


@pytest.mark.parametrize(
    "filename, default_ft",
    [
        ("foo.json", None),
        ("foo.json", "json"),
        ("foo.json", "yaml"),
        ("foo", "json"),
        # YAML is a superset of JSON, so using the YAML loader should be safe when the
        # data is JSON
        ("foo", "yaml"),
    ],
)
def test_instanceloader_json_data(tmp_path, filename, default_ft):
    f = tmp_path / filename
    f.write_text("{}")
    loader = InstanceLoader([str(f)], default_filetype=default_ft)
    data = list(loader.iter_files())
    assert data == [(str(f), {})]


@pytest.mark.parametrize(
    "filename, default_ft",
    [
        ("foo.yaml", None),
        ("foo.yml", None),
        ("foo.yaml", "json"),
        ("foo.yml", "json"),
        ("foo.yaml", "yaml"),
        ("foo.yml", "yaml"),
        ("foo", "yaml"),
    ],
)
def test_instanceloader_yaml_data(tmp_path, filename, default_ft):
    f = tmp_path / filename
    f.write_text(
        """\
a:
  b: &anchor
   - 1
   - 2
  c: &anchor d
"""
    )
    loader = InstanceLoader([str(f)], default_filetype=default_ft)
    data = list(loader.iter_files())
    assert data == [(str(f), {"a": {"b": [1, 2], "c": "d"}})]


def test_instanceloader_unknown_type(tmp_path):
    f = tmp_path / "foo"  # no extension here
    f.write_text("{}")  # json data (could be detected as either)
    loader = InstanceLoader([str(f)])
    # at iteration time, the file should error
    with pytest.raises(BadFileTypeError):
        list(loader.iter_files())


@pytest.mark.parametrize(
    "enabled_flag, extension, file_content, expect_data, expect_error_message",
    [
        (
            JSON5_ENABLED,
            "json5",
            "{}",
            {},
            "pip install json5",
        ),
        (
            TOML_ENABLED,
            "toml",
            '[foo]\nbar = "baz"\n',
            {"foo": {"bar": "baz"}},
            "pip install tomli",
        ),
    ],
)
def test_instanceloader_optional_format_handling(
    tmp_path, enabled_flag, extension, file_content, expect_data, expect_error_message
):
    f = tmp_path / f"foo.{extension}"
    f.write_text(file_content)
    loader = InstanceLoader([str(f)])
    if enabled_flag:
        # at iteration time, the file should load fine
        data = list(loader.iter_files())
        assert data == [(str(f), expect_data)]
    else:
        # at iteration time, an error should be raised
        with pytest.raises(BadFileTypeError) as excinfo:
            list(loader.iter_files())

        err = excinfo.value
        # error message should be instructive
        assert expect_error_message in str(err)
