import json
import os
import platform
import time

import pytest
import requests
import responses

from check_jsonschema.cachedownloader import (
    CacheDownloader,
    FailedDownloadError,
    _cache_hit,
)


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
    cd = CacheDownloader().bind("https://example.com/schema1.json")
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

    cd = CacheDownloader()
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
    assert _cache_hit(
        "/tmp/schema1.json",
        requests.get("https://example.com/schema1.json", stream=True),
    )

    # local mtime = 0, cache miss
    monkeypatch.setattr(os.path, "getmtime", lambda x: 0)
    assert (
        _cache_hit(
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
    cd = CacheDownloader(cache_dir=tmp_path).bind(str(f))
    # patch the downloader to skip any download "work"
    monkeypatch.setattr(cd._downloader, "_download", lambda file_uri, filename: str(f))

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
        cd = CacheDownloader(cache_dir=str(tmp_path)).bind(
            "https://example.com/schema1.json", filename=str(f)
        )
    elif mode == "filename_otherdir":
        otherdir = tmp_path / "otherdir"
        cd = CacheDownloader(cache_dir=str(otherdir)).bind(
            "https://example.com/schema1.json", filename=str(f)
        )
    elif mode == "cache_dir":
        cd = CacheDownloader(cache_dir=str(tmp_path)).bind(
            "https://example.com/schema1.json"
        )
    elif mode == "disable_cache":
        cd = CacheDownloader(disable_cache=True).bind(
            "https://example.com/schema1.json"
        )
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
        cache_dir=str(tmp_path),
        disable_cache=disable_cache,
        validation_callback=json.loads,
    ).bind("https://example.com/schema1.json", filename=str(f))

    with cd.open() as fp:
        assert fp.read() == b"{}"

    if disable_cache:
        assert not f.exists()
    else:
        assert f.exists()


@pytest.mark.parametrize("file_exists", (True, False))
@pytest.mark.parametrize(
    "failure_mode", ("header_missing", "header_malformed", "time_overflow")
)
def test_cachedownloader_handles_bad_lastmod_header(
    monkeypatch, tmp_path, file_exists, failure_mode
):
    if failure_mode == "header_missing":
        responses.add(
            "GET",
            "https://example.com/schema1.json",
            headers={},
            json={},
            match_querystring=None,
        )
    elif failure_mode == "header_malformed":
        responses.add(
            "GET",
            "https://example.com/schema1.json",
            headers={"Last-Modified": "Jan 2000 00:00:01"},
            json={},
            match_querystring=None,
        )
    elif failure_mode == "time_overflow":
        add_default_response()

        def fake_mktime(*args):
            raise OverflowError("uh-oh")

        monkeypatch.setattr("time.mktime", fake_mktime)
    else:
        raise NotImplementedError

    original_file_contents = b'{"foo": "bar"}'
    f = tmp_path / "schema1.json"

    if file_exists:
        f.write_bytes(original_file_contents)
    else:
        assert not f.exists()

    cd = CacheDownloader(cache_dir=str(tmp_path)).bind(
        "https://example.com/schema1.json", filename=str(f)
    )

    # if the file already existed, it will not be overwritten by the cachedownloader
    # so the returned value for both the downloader and a direct file read should be the
    # original contents
    if file_exists:
        with cd.open() as fp:
            assert fp.read() == original_file_contents
        assert f.read_bytes() == original_file_contents
    # otherwise, the file will have been created with new content
    # both reads will show that new content
    else:
        with cd.open() as fp:
            assert fp.read() == b"{}"
        assert f.read_bytes() == b"{}"

    # at the end, the file always exists on disk
    assert f.exists()


def test_cachedownloader_validation_is_not_invoked_on_hit(monkeypatch, tmp_path):
    """
    Regression test for https://github.com/python-jsonschema/check-jsonschema/issues/453

    This was a bug in which the validation callback was invoked eagerly, even on a cache
    hit. As a result, cache hits did not demonstrate their expected performance gain.
    """
    # 1: construct some perfectly good data (it doesn't really matter what it is)
    add_default_response()
    # 2: put equivalent data on disk
    f = tmp_path / "schema1.json"
    f.write_text("{}")

    # 3: construct a validator which marks that it ran in a variable
    validator_ran = False

    def dummy_validate_bytes(data):
        nonlocal validator_ran
        validator_ran = True

    # construct a downloader pointed at the schema and file, expecting a cache hit
    # and use the above validation method
    cd = CacheDownloader(
        cache_dir=str(tmp_path), validation_callback=dummy_validate_bytes
    ).bind("https://example.com/schema1.json", filename=str(f))

    # read data from the downloader
    with cd.open() as fp:
        assert fp.read() == b"{}"
    # assert that the validator was not run
    assert validator_ran is False
