import os
import pathlib
import platform

import pytest

from check_jsonschema.loaders import BadFileTypeError, InstanceLoader, SchemaLoader


class FakePathlibPath:
    def __init__(self, path):
        self._path = path

    def __str__(self):
        return self._path

    def expanduser(self):
        if self._path.startswith("~/"):
            return FakePathlibPath(os.path.join("/home/dummy-user", self._path[2:]))
        return self

    def resolve(self):
        return self


@pytest.mark.parametrize(
    "schemafile",
    [
        "https://foo.example.com/schema.json",
        "http://foo.example.com/schema.json",
        "path/to/schema.json",
    ],
)
def test_schemaloader_expanduser_no_op(schemafile):
    sl = SchemaLoader(schemafile)
    if schemafile.startswith("http"):
        assert sl._filename == schemafile
        assert sl._downloader is not None
    else:
        assert sl._filename == os.path.abspath(schemafile)
        assert sl._downloader is None


def test_schemaloader_expanduser(monkeypatch):
    if platform.system() == "Windows":
        pytest.skip("skip this test on windows for simplicity")

    monkeypatch.setattr(pathlib, "Path", FakePathlibPath)

    sl = SchemaLoader("~/schema1.json")
    assert sl._filename == "/home/dummy-user/schema1.json"
    assert sl._downloader is None

    sl = SchemaLoader("somepath/schema1.json")
    assert sl._filename == "somepath/schema1.json"
    assert sl._downloader is None


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
