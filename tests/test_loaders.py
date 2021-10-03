import os
import platform

import pytest

from check_jsonschema.loaders import SchemaLoader


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
    assert sl._filename == schemafile
    if schemafile.startswith("http"):
        assert sl._downloader is not None
    else:
        assert sl._downloader is None


def test_schemaloader_expanduser(monkeypatch):
    if platform.system() == "Windows":
        pytest.skip("skip this test on windows for simplicity")

    def fake_expanduser(path):
        if path.startswith("~/"):
            return os.path.join("/home/dummy-user", path[2:])
        return path

    monkeypatch.setattr(os.path, "expanduser", fake_expanduser)

    sl = SchemaLoader("~/schema1.json")
    assert sl._filename == "/home/dummy-user/schema1.json"
    assert sl._downloader is None

    sl = SchemaLoader("somepath/schema1.json")
    assert sl._filename == "somepath/schema1.json"
    assert sl._downloader is None
