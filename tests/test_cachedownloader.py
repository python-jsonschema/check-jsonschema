import os
import platform
import time

import pytest

from check_jsonschema.cachedownloader import CacheDownloader


class DummyConnHeaders:
    def __init__(self):
        self.lastmod = "Sun, 01 Jan 2000 00:00:01 GMT"

    def get(self, name, default):
        if name.lower() == "last-modified":
            if self.lastmod:
                return self.lastmod
        return default


class DummyConn:
    def __init__(self):
        self.headers = DummyConnHeaders()


def test_default_filename_from_uri():
    cd = CacheDownloader("https://foo.example.com/schema1.json")
    assert cd._filename == "schema1.json"


@pytest.mark.parametrize(
    "sysname, fakeenv, expect_value",
    [
        ("Windows", {}, None),
        (
            "Windows",
            {"LOCALAPPDATA": "localappdata", "APPDATA": "appdata"},
            "localappdata",
        ),
        ("Windows", {"LOCALAPPDATA": "localappdata"}, "localappdata"),
        ("Windows", {"APPDATA": "appdata"}, "appdata"),
        ("Darwin", {}, "<expanduser>"),
        ("Linux", {}, "<expanduser>"),
        ("Linux", {"XDG_CACHE_HOME": "xdg-cache"}, "xdg-cache"),
    ],
)
def test_default_cache_dir(monkeypatch, sysname, fakeenv, expect_value):
    for var in ["LOCALAPPDATA", "APPDATA", "XDG_CACHE_HOME"]:
        monkeypatch.delenv(var, raising=False)
    for k, v in fakeenv.items():
        monkeypatch.setenv(k, v)
    if expect_value is not None:
        expect_value = os.path.join(expect_value, "check_jsonschema", "downloads")

    def fakesystem():
        return sysname

    expanduser_path = None

    def fake_expanduser(path):
        nonlocal expanduser_path
        expanduser_path = path
        return "<expanduser>"

    monkeypatch.setattr(platform, "system", fakesystem)
    monkeypatch.setattr(os.path, "expanduser", fake_expanduser)

    cd = CacheDownloader("https://example.com/foo-schema.json")
    assert cd._cache_dir == expect_value

    if sysname == "Darwin":
        assert expanduser_path == "~/Library/Caches"
    elif sysname == "Linux":
        assert expanduser_path == "~/.cache"
    else:
        assert expanduser_path is None


def test_cache_hit_by_mtime(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda x: True)

    # local mtime = NOW, cache hit
    monkeypatch.setattr(os.path, "getmtime", lambda x: time.time())
    cd = CacheDownloader("https://foo.example.com/schema1.json")
    assert cd._cache_hit("/tmp/schema1.json", DummyConn())

    # local mtime = 0, cache miss
    monkeypatch.setattr(os.path, "getmtime", lambda x: 0)
    cd = CacheDownloader("https://foo.example.com/schema1.json")
    assert cd._cache_hit("/tmp/schema1.json", DummyConn()) is False


def test_cachedownloader_cached_file(tmp_path, monkeypatch):
    # create a file
    f = tmp_path / "foo.json"
    f.write_text("{}")

    # set the cache_dir to the tmp dir (so that cache_dir will always be set)
    cd = CacheDownloader(str(f), cache_dir=tmp_path)
    # patch the downloader to skip any download "work"
    monkeypatch.setattr(cd, "_download", lambda: str(f))

    with cd.open() as fp:
        assert fp.read() == "{}"
