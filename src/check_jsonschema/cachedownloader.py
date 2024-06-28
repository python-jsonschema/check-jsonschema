from __future__ import annotations

import contextlib
import io
import os
import platform
import shutil
import tempfile
import time
import typing as t

import requests

# this will let us do any other caching we might need in the future in the same
# cache dir (adjacent to "downloads")
_CACHEDIR_NAME = os.path.join("check_jsonschema", "downloads")

_LASTMOD_FMT = "%a, %d %b %Y %H:%M:%S %Z"


def _get_default_cache_dir() -> str | None:
    sysname = platform.system()

    # on windows, try to get the appdata env var
    # this *could* result in cache_dir=None, which is fine, just skip caching in
    # that case
    if sysname == "Windows":
        cache_dir = os.getenv("LOCALAPPDATA", os.getenv("APPDATA"))
    # macOS -> app support dir
    elif sysname == "Darwin":
        cache_dir = os.path.expanduser("~/Library/Caches")
    # default for unknown platforms, namely linux behavior
    # use XDG env var and default to ~/.cache/
    else:
        cache_dir = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))

    if cache_dir:
        cache_dir = os.path.join(cache_dir, _CACHEDIR_NAME)

    return cache_dir


def _lastmod_from_response(response: requests.Response) -> float:
    try:
        return time.mktime(
            time.strptime(response.headers["last-modified"], _LASTMOD_FMT)
        )
    # OverflowError: time outside of platform-specific bounds
    # ValueError: malformed/unparseable
    # LookupError: no such header
    except (OverflowError, ValueError, LookupError):
        return 0.0


def _get_request(
    file_url: str, *, response_ok: t.Callable[[requests.Response], bool]
) -> requests.Response:
    try:
        r: requests.Response | None = None
        for _attempt in range(3):
            r = requests.get(file_url, stream=True)
            if r.ok and response_ok(r):
                return r
        assert r is not None
        raise FailedDownloadError(
            f"got response with status={r.status_code}, retries exhausted"
        )
    except requests.RequestException as e:
        raise FailedDownloadError("encountered error during download") from e


def _atomic_write(dest: str, content: bytes) -> None:
    # download to a temp file and then move to the dest
    # this makes the download safe if run in parallel (parallel runs
    # won't create a new empty file for writing and cause failures)
    fp = tempfile.NamedTemporaryFile(mode="wb", delete=False)
    fp.write(content)
    fp.close()
    shutil.copy(fp.name, dest)
    os.remove(fp.name)


def _cache_hit(cachefile: str, response: requests.Response) -> bool:
    # no file? miss
    if not os.path.exists(cachefile):
        return False

    # compare mtime on any cached file against the remote last-modified time
    # it is considered a hit if the local file is at least as new as the remote file
    local_mtime = os.path.getmtime(cachefile)
    remote_mtime = _lastmod_from_response(response)
    return local_mtime >= remote_mtime


class FailedDownloadError(Exception):
    pass


class CacheDownloader:
    def __init__(
        self,
        cache_dir: str | None = None,
        disable_cache: bool = False,
        validation_callback: t.Callable[[bytes], t.Any] | None = None,
    ):
        self._cache_dir = cache_dir or _get_default_cache_dir()
        self._disable_cache = disable_cache
        self._validation_callback = validation_callback

    def _validate(self, response: requests.Response) -> bool:
        if not self._validation_callback:
            return True

        try:
            self._validation_callback(response.content)
            return True
        except ValueError:
            return False

    def _download(self, file_url: str, filename: str) -> str:
        assert self._cache_dir is not None
        os.makedirs(self._cache_dir, exist_ok=True)
        dest = os.path.join(self._cache_dir, filename)

        def check_response_for_download(r: requests.Response) -> bool:
            # if the response indicates a cache hit, treat it as valid
            # this ensures that we short-circuit any further evaluation immediately on
            # a hit
            if _cache_hit(dest, r):
                return True
            # we now know it's not a hit, so validate the content (forces download)
            return self._validate(r)

        response = _get_request(file_url, response_ok=check_response_for_download)
        # check to see if we have a file which matches the connection
        # only download if we do not (cache miss, vs hit)
        if not _cache_hit(dest, response):
            _atomic_write(dest, response.content)

        return dest

    @contextlib.contextmanager
    def open(self, file_url: str, filename: str) -> t.Iterator[t.IO[bytes]]:
        if (not self._cache_dir) or self._disable_cache:
            yield io.BytesIO(_get_request(file_url, response_ok=self._validate).content)
        else:
            with open(self._download(file_url, filename), "rb") as fp:
                yield fp

    def bind(self, file_url: str, filename: str | None = None) -> BoundCacheDownloader:
        return BoundCacheDownloader(file_url, filename, self)


class BoundCacheDownloader:
    def __init__(
        self,
        file_url: str,
        filename: str | None,
        downloader: CacheDownloader,
    ):
        self._file_url = file_url
        self._filename = filename or file_url.split("/")[-1]
        self._downloader = downloader

    @contextlib.contextmanager
    def open(self) -> t.Iterator[t.IO[bytes]]:
        with self._downloader.open(self._file_url, self._filename) as fp:
            yield fp
