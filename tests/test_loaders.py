import os
import pathlib
import platform

import pytest

from check_jsonschema.loaders import BadFileTypeError, InstanceLoader, SchemaLoader
from check_jsonschema.loaders.schema import HttpSchemaReader, LocalSchemaReader


def test_schemaloader_path_handling_relative_local_path():
    path = "path/to/schema.json"
    sl = SchemaLoader(path)
    assert isinstance(sl._reader, LocalSchemaReader)
    assert sl._reader._filename == os.path.abspath(path)


@pytest.mark.parametrize(
    "schemafile",
    [
        "https://foo.example.com/schema.json",
        "http://foo.example.com/schema.json",
    ],
)
def test_schemaloader_remote_path(schemafile):
    sl = SchemaLoader(schemafile)
    assert isinstance(sl._reader, HttpSchemaReader)
    assert sl._reader._url == schemafile


def test_schemaloader_expanduser(monkeypatch):
    if platform.system() == "Windows":
        pytest.skip("skip this test on windows for simplicity")

    def fake_resolve(path):
        path = str(path)
        if path.startswith("~/"):
            path = os.path.join("/home/dummy-user/", path[2:])
            return pathlib.Path(path)
        else:
            path = os.path.join("/dummy/abs/path/", path)
            return pathlib.Path(path)

    monkeypatch.setattr("check_jsonschema.loaders.schema._resolve_path", fake_resolve)

    sl = SchemaLoader("~/schema1.json")
    assert isinstance(sl._reader, LocalSchemaReader)
    assert sl._reader._filename == "/home/dummy-user/schema1.json"

    sl = SchemaLoader("somepath/schema1.json")
    assert isinstance(sl._reader, LocalSchemaReader)
    assert sl._reader._filename == "/dummy/abs/path/somepath/schema1.json"


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
  b:
   - 1
   - 2
  c: d
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
