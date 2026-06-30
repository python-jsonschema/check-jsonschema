import json
import os
import platform

import pytest
import requests
import responses

from check_jsonschema.cachedownloader import (
    CacheDownloader,
    FailedDownloadError,
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


@pytest.mark.parametrize("disable_cache", (True, False))
def test_cachedownloader_on_success(
    disable_cache, default_response, downloads_cache_dir
):
    cd = CacheDownloader("downloads", disable_cache=disable_cache).bind(
        DEFAULT_RESPONSE_URL
    )

    with cd.open() as fp:
        assert fp.read() == b"{}"
    if disable_cache:
        assert not downloads_cache_dir.exists()
    else:
        assert downloads_cache_dir.exists()


def test_cachedownloader_using_alternate_target_dir(cache_dir, default_response):
    cd = CacheDownloader("otherdir").bind(DEFAULT_RESPONSE_URL)
    with cd.open() as fp:
        assert fp.read() == b"{}"

    # Cache directory is created for the alternate target dir
    assert cache_dir.joinpath("check_jsonschema", "otherdir").exists()


@pytest.mark.parametrize("disable_cache", (True, False))
@pytest.mark.parametrize("failures", (1, 2, requests.ConnectionError))
def test_cachedownloader_succeeds_after_few_errors(
    disable_cache, failures, downloads_cache_dir
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
    cd = CacheDownloader("downloads", disable_cache=disable_cache).bind(
        DEFAULT_RESPONSE_URL
    )

    with cd.open() as fp:
        assert fp.read() == b"{}"
    if disable_cache:
        assert not downloads_cache_dir.exists()
    else:
        assert downloads_cache_dir.exists()


@pytest.mark.parametrize("disable_cache", (True, False))
@pytest.mark.parametrize("connection_error", (True, False))
def test_cachedownloader_fails_after_many_errors(
    disable_cache, connection_error, downloads_cache_dir
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
    cd = CacheDownloader("downloads", disable_cache=disable_cache).bind(
        DEFAULT_RESPONSE_URL
    )
    with pytest.raises(FailedDownloadError):
        with cd.open():
            pass

    # Cache directory is created only when caching is enabled
    # (even though the request failed, the session was built)
    assert downloads_cache_dir.exists() is not disable_cache


@pytest.mark.parametrize("disable_cache", (True, False))
def test_cachedownloader_retries_on_bad_data(disable_cache, downloads_cache_dir):
    responses.add(
        "GET",
        DEFAULT_RESPONSE_URL,
        status=200,
        body="{",
        match_querystring=None,
    )
    add_default_response()
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
        assert not downloads_cache_dir.exists()
    else:
        assert downloads_cache_dir.exists()


def test_disable_cache_uses_plain_session():
    """When disable_cache=True, verify _session returns a plain Session."""
    cd = CacheDownloader("downloads", disable_cache=True)
    session = cd._session
    # A plain requests.Session does not have CacheControlAdapter
    assert type(session) is requests.Session


def test_enable_cache_uses_cachecontrol_session(tmp_path, patch_cache_dir):
    """When disable_cache=False, verify _session returns a CacheControl session."""
    from cachecontrol import CacheControlAdapter

    cd = CacheDownloader("downloads", disable_cache=False)
    session = cd._session
    # CacheControl wraps the session and attaches CacheControlAdapter
    assert isinstance(session.get_adapter("https://"), CacheControlAdapter)
    assert isinstance(session.get_adapter("http://"), CacheControlAdapter)


def test_cache_dir_none_uses_plain_session(monkeypatch, patch_cache_dir):
    """When _resolve_cache_dir returns None, _session returns plain Session."""
    # Undo the patch and simulate Windows with no env vars
    patch_cache_dir.undo()
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    cd = CacheDownloader("downloads", disable_cache=False)
    assert cd._cache_dir is None
    session = cd._session
    assert type(session) is requests.Session
