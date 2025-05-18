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
    _lastmod_from_response,
    url_to_cache_filename,
)

DEFAULT_RESPONSE_URL = "https://example.com/schema1.json"
DEFAULT_LASTMOD = "Sun, 01 Jan 2000 00:00:01 GMT"


def add_default_response():
    responses.add(
        "GET",
        DEFAULT_RESPONSE_URL,
        headers={"Last-Modified": DEFAULT_LASTMOD},
        json={},
        match_querystring=None,
    )


@pytest.fixture
def default_response():
    add_default_response()


def test_default_filename_from_uri(default_response):
    cd = CacheDownloader("downloads").bind(DEFAULT_RESPONSE_URL)
    assert cd._filename == url_to_cache_filename(DEFAULT_RESPONSE_URL)


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
    patch_cache_dir, monkeypatch, default_response, sysname, fakeenv, expect_value
):
    # undo the patch which typically overrides resolution of the cache dir
    patch_cache_dir.undo()

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

    cd = CacheDownloader("downloads")
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
        requests.get(DEFAULT_RESPONSE_URL, stream=True),
    )

    # local mtime = 0, cache miss
    monkeypatch.setattr(os.path, "getmtime", lambda x: 0)
    assert (
        _cache_hit(
            "/tmp/schema1.json",
            requests.get(DEFAULT_RESPONSE_URL, stream=True),
        )
        is False
    )


def test_cachedownloader_cached_file(tmp_path, monkeypatch, default_response):
    # create a file
    f = tmp_path / "foo.json"
    f.write_text("{}")

    # set the cache_dir to the tmp dir (so that cache_dir will always be set)
    cd = CacheDownloader(tmp_path).bind(str(f), filename="foo.json")
    # patch the downloader to skip any download "work"
    monkeypatch.setattr(
        cd._downloader, "_download", lambda file_uri, filename, response_ok: str(f)
    )

    with cd.open() as fp:
        assert fp.read() == b"{}"


@pytest.mark.parametrize("disable_cache", (True, False))
def test_cachedownloader_on_success(
    get_download_cache_loc, disable_cache, default_response
):
    f = get_download_cache_loc(DEFAULT_RESPONSE_URL)
    cd = CacheDownloader("downloads", disable_cache=disable_cache).bind(
        DEFAULT_RESPONSE_URL
    )

    with cd.open() as fp:
        assert fp.read() == b"{}"
    if disable_cache:
        assert not f.exists()
    else:
        assert f.exists()


def test_cachedownloader_using_alternate_target_dir(
    cache_dir, default_response, url2cachepath
):
    cache_dir = cache_dir / "check_jsonschema" / "otherdir"
    f = url2cachepath(cache_dir, DEFAULT_RESPONSE_URL)
    cd = CacheDownloader("otherdir").bind(DEFAULT_RESPONSE_URL)
    with cd.open() as fp:
        assert fp.read() == b"{}"
    assert f.exists()


@pytest.mark.parametrize("disable_cache", (True, False))
@pytest.mark.parametrize("failures", (1, 2, requests.ConnectionError))
def test_cachedownloader_succeeds_after_few_errors(
    get_download_cache_loc, disable_cache, failures
):
    if isinstance(failures, int):
        for _i in range(failures):
            responses.add(
                "GET",
                DEFAULT_RESPONSE_URL,
                status=500,
                match_querystring=None,
            )
    else:
        responses.add(
            "GET",
            DEFAULT_RESPONSE_URL,
            body=failures(),
            match_querystring=None,
        )
    add_default_response()
    f = get_download_cache_loc(DEFAULT_RESPONSE_URL)
    cd = CacheDownloader("downloads", disable_cache=disable_cache).bind(
        DEFAULT_RESPONSE_URL
    )

    with cd.open() as fp:
        assert fp.read() == b"{}"
    if disable_cache:
        assert not f.exists()
    else:
        assert f.exists()


@pytest.mark.parametrize("disable_cache", (True, False))
@pytest.mark.parametrize("connection_error", (True, False))
def test_cachedownloader_fails_after_many_errors(
    get_download_cache_loc, disable_cache, connection_error
):
    for _i in range(10):
        if connection_error:
            responses.add(
                "GET",
                DEFAULT_RESPONSE_URL,
                body=requests.ConnectionError(),
                match_querystring=None,
            )
        else:
            responses.add(
                "GET",
                DEFAULT_RESPONSE_URL,
                status=500,
                match_querystring=None,
            )
    add_default_response()  # never reached, the 11th response
    f = get_download_cache_loc(DEFAULT_RESPONSE_URL)
    cd = CacheDownloader("downloads", disable_cache=disable_cache).bind(
        DEFAULT_RESPONSE_URL
    )
    with pytest.raises(FailedDownloadError):
        with cd.open():
            pass
    assert not f.exists()


@pytest.mark.parametrize("disable_cache", (True, False))
def test_cachedownloader_retries_on_bad_data(get_download_cache_loc, disable_cache):
    responses.add(
        "GET",
        DEFAULT_RESPONSE_URL,
        status=200,
        body="{",
        match_querystring=None,
    )
    add_default_response()
    f = get_download_cache_loc(DEFAULT_RESPONSE_URL)
    cd = CacheDownloader(
        "downloads",
        disable_cache=disable_cache,
    ).bind(
        DEFAULT_RESPONSE_URL,
        validation_callback=json.loads,
    )

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
    monkeypatch,
    get_download_cache_loc,
    inject_cached_download,
    file_exists,
    failure_mode,
):
    if failure_mode == "header_missing":
        responses.add(
            "GET", DEFAULT_RESPONSE_URL, headers={}, json={}, match_querystring=None
        )
    elif failure_mode == "header_malformed":
        responses.add(
            "GET",
            DEFAULT_RESPONSE_URL,
            headers={"Last-Modified": "Jan 2000 00:00:01"},
            json={},
            match_querystring=None,
        )
    elif failure_mode == "time_overflow":
        add_default_response()

        def fake_timegm(*args):
            raise OverflowError("uh-oh")

        monkeypatch.setattr("calendar.timegm", fake_timegm)
    else:
        raise NotImplementedError

    original_file_contents = b'{"foo": "bar"}'
    file_path = get_download_cache_loc(DEFAULT_RESPONSE_URL)

    assert not file_path.exists()
    if file_exists:
        inject_cached_download(DEFAULT_RESPONSE_URL, original_file_contents)

    cd = CacheDownloader("downloads").bind(DEFAULT_RESPONSE_URL)

    # if the file already existed, it will not be overwritten by the cachedownloader
    # so the returned value for both the downloader and a direct file read should be the
    # original contents
    if file_exists:
        with cd.open() as fp:
            assert fp.read() == original_file_contents
        assert file_path.read_bytes() == original_file_contents
    # otherwise, the file will have been created with new content
    # both reads will show that new content
    else:
        with cd.open() as fp:
            assert fp.read() == b"{}"
        assert file_path.read_bytes() == b"{}"

    # at the end, the file always exists on disk
    assert file_path.exists()


def test_cachedownloader_validation_is_not_invoked_on_hit(
    monkeypatch, default_response, inject_cached_download
):
    """
    Regression test for https://github.com/python-jsonschema/check-jsonschema/issues/453

    This was a bug in which the validation callback was invoked eagerly, even on a cache
    hit. As a result, cache hits did not demonstrate their expected performance gain.
    """
    # 1: construct some perfectly good data (it doesn't really matter what it is)
    #    <<default_response fixture>>
    # 2: put equivalent data on disk
    inject_cached_download(DEFAULT_RESPONSE_URL, "{}")

    # 3: construct a validator which marks that it ran in a variable
    validator_ran = False

    def dummy_validate_bytes(data):
        nonlocal validator_ran
        validator_ran = True

    # construct a downloader pointed at the schema and file, expecting a cache hit
    # and use the above validation method
    cd = CacheDownloader("downloads").bind(
        DEFAULT_RESPONSE_URL,
        validation_callback=dummy_validate_bytes,
    )

    # read data from the downloader
    with cd.open() as fp:
        assert fp.read() == b"{}"
    # assert that the validator was not run
    assert validator_ran is False


def test_lastmod_from_header_uses_gmtime(request, monkeypatch, default_response):
    """
    Regression test for https://github.com/python-jsonschema/check-jsonschema/pull/565

    The time was converted in local time, when UTC/GMT was desired.
    """

    def final_tzset():
        time.tzset()

    request.addfinalizer(final_tzset)

    response = requests.get(DEFAULT_RESPONSE_URL, stream=True)

    with monkeypatch.context() as m:
        m.setenv("TZ", "GMT0")
        time.tzset()
        gmt_parsed_time = _lastmod_from_response(response)

    with monkeypatch.context() as m:
        m.setenv("TZ", "EST5")
        time.tzset()
        est_parsed_time = _lastmod_from_response(response)

    with monkeypatch.context() as m:
        m.setenv("TZ", "UTC0")
        time.tzset()
        utc_parsed_time = _lastmod_from_response(response)

    # assert that they all match
    assert gmt_parsed_time == utc_parsed_time
    assert gmt_parsed_time == est_parsed_time
