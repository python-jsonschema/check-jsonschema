import json
import os
import platform
import time

import pytest
import requests
import responses

from check_jsonschema.cachedownloader import CacheDownloader, FailedDownloadError


def add_default_response():
    responses.add(
        "GET",
        "https://example.com/schema1.json",
        headers={"Last-Modified": "Sun, 01 Jan 2000 00:00:01 GMT"},
        json={},
        match_querystring=None,
    )


@pytest.fixture
def default_response():
    add_default_response()


def test_default_filename_from_uri(default_response):
    cd = CacheDownloader("https://example.com/schema1.json")
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
def test_default_cache_dir(
    monkeypatch, default_response, sysname, fakeenv, expect_value
):
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

    cd = CacheDownloader("https://example.com/schema1.json")
    assert cd._cache_dir == expect_value

    if sysname == "Darwin":
        assert expanduser_path == "~/Library/Caches"
    elif sysname == "Linux":
        assert expanduser_path == "~/.cache"
    else:
        assert expanduser_path is None


def test_cache_hit_by_mtime(monkeypatch, default_response):
    monkeypatch.setattr(os.path, "exists", lambda x: True)

    # local mtime = NOW, cache hit
    monkeypatch.setattr(os.path, "getmtime", lambda x: time.time())
    cd = CacheDownloader("https://example.com/schema1.json")
    assert cd._cache_hit(
        "/tmp/schema1.json",
        requests.get("https://example.com/schema1.json", stream=True),
    )

    # local mtime = 0, cache miss
    monkeypatch.setattr(os.path, "getmtime", lambda x: 0)
    cd = CacheDownloader("https://example.com/schema1.json")
    assert (
        cd._cache_hit(
            "/tmp/schema1.json",
            requests.get("https://example.com/schema1.json", stream=True),
        )
        is False
    )


def test_cachedownloader_cached_file(tmp_path, monkeypatch, default_response):
    # create a file
    f = tmp_path / "foo.json"
    f.write_text("{}")

    # set the cache_dir to the tmp dir (so that cache_dir will always be set)
    cd = CacheDownloader(str(f), cache_dir=tmp_path)
    # patch the downloader to skip any download "work"
    monkeypatch.setattr(cd, "_download", lambda: str(f))

    with cd.open() as fp:
        assert fp.read() == b"{}"


@pytest.mark.parametrize(
    "mode", ["filename", "filename_otherdir", "cache_dir", "disable_cache"]
)
@pytest.mark.parametrize("failures", (0, 1, 10, requests.ConnectionError))
def test_cachedownloader_e2e(tmp_path, mode, failures):
    if isinstance(failures, int):
        for _i in range(failures):
            responses.add(
                "GET",
                "https://example.com/schema1.json",
                status=500,
                match_querystring=None,
            )
    else:
        responses.add(
            "GET",
            "https://example.com/schema1.json",
            body=failures(),
            match_querystring=None,
        )
    add_default_response()
    f = tmp_path / "schema1.json"
    if mode == "filename":
        cd = CacheDownloader(
            "https://example.com/schema1.json", filename=str(f), cache_dir=str(tmp_path)
        )
    elif mode == "filename_otherdir":
        otherdir = tmp_path / "otherdir"
        cd = CacheDownloader(
            "https://example.com/schema1.json", filename=str(f), cache_dir=str(otherdir)
        )
    elif mode == "cache_dir":
        cd = CacheDownloader(
            "https://example.com/schema1.json", cache_dir=str(tmp_path)
        )
    elif mode == "disable_cache":
        cd = CacheDownloader("https://example.com/schema1.json", disable_cache=True)
    else:
        raise NotImplementedError

    if isinstance(failures, int) and failures < 3:
        with cd.open() as fp:
            assert fp.read() == b"{}"
        if mode == "filename":
            assert f.exists()
        elif mode == "filename_otherdir":
            otherdir = f.exists()
        elif mode == "cache_dir":
            assert (tmp_path / "schema1.json").exists()
        elif mode == "disable_cache":
            assert not (tmp_path / "schema1.json").exists()
            assert not f.exists()
        else:
            raise NotImplementedError
    else:
        with pytest.raises(FailedDownloadError):
            with cd.open() as fp:
                pass
        assert not (tmp_path / "schema1.json").exists()
        assert not f.exists()


@pytest.mark.parametrize("disable_cache", (True, False))
def test_cachedownloader_retries_on_bad_data(tmp_path, disable_cache):
    responses.add(
        "GET",
        "https://example.com/schema1.json",
        status=200,
        body="{",
        match_querystring=None,
    )
    add_default_response()
    f = tmp_path / "schema1.json"
    cd = CacheDownloader(
        "https://example.com/schema1.json",
        filename=str(f),
        cache_dir=str(tmp_path),
        disable_cache=disable_cache,
        validation_callback=json.loads,
    )

    with cd.open() as fp:
        assert fp.read() == b"{}"

    if disable_cache:
        assert not f.exists()
    else:
        assert f.exists()
