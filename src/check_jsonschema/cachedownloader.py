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


class FailedDownloadError(Exception):
    pass


class CacheDownloader:
    _LASTMOD_DEFAULT = "Sun, 01 Jan 1970 00:00:01 GMT"
    _LASTMOD_FMT = "%a, %d %b %Y %H:%M:%S %Z"

    # changed in v0.5.0
    # original cache dir was "jsonschema_validate"
    # this will let us do any other caching we might need in the future in the same
    # cache dir (adjacent to "downloads")
    _CACHEDIR_NAME = os.path.join("check_jsonschema", "downloads")

    def __init__(
        self,
        file_url: str,
        filename: str | None = None,
        cache_dir: str | None = None,
        disable_cache: bool = False,
        validation_callback: t.Callable[[bytes], t.Any] | None = None,
    ):
        self._file_url = file_url
        self._filename = filename or file_url.split("/")[-1]
        self._cache_dir = cache_dir or self._compute_default_cache_dir()
        self._disable_cache = disable_cache
        self._validation_callback = validation_callback

    def _compute_default_cache_dir(self) -> str | None:
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
            cache_dir = os.path.join(cache_dir, self._CACHEDIR_NAME)

        return cache_dir

    def _get_request(self) -> requests.Response:
        try:
            # do manual retries, rather than using urllib3 retries, to make it trivially
            # testable with 'responses'
            r: requests.Response | None = None
            for _attempt in range(3):
                r = requests.get(self._file_url, stream=True)
                if r.ok:
                    if self._validation_callback is not None:
                        try:
                            self._validation_callback(r.content)
                        except ValueError:
                            continue
                    return r
            assert r is not None
            raise FailedDownloadError(
                f"got responses with status={r.status_code}, retries exhausted"
            )
        except requests.RequestException as e:
            raise FailedDownloadError("encountered error during download") from e

    def _lastmod_from_response(self, response: requests.Response) -> float:
        return time.mktime(
            time.strptime(
                response.headers.get("last-modified", self._LASTMOD_DEFAULT),
                self._LASTMOD_FMT,
            )
        )

    def _cache_hit(self, cachefile: str, response: requests.Response) -> bool:
        # no file? miss
        if not os.path.exists(cachefile):
            return False

        # compare mtime on any cached file against the remote last-modified time
        # it is considered a hit if the local file is at least as new as the remote file
        local_mtime = os.path.getmtime(cachefile)
        remote_mtime = self._lastmod_from_response(response)
        return local_mtime >= remote_mtime

    def _write(self, dest: str, response: requests.Response) -> None:
        # download to a temp file and then move to the dest
        # this makes the download safe if run in parallel (parallel runs
        # won't create a new empty file for writing and cause failures)
        fp = tempfile.NamedTemporaryFile(mode="wb", delete=False)
        fp.write(response.content)
        fp.close()
        shutil.copy(fp.name, dest)
        os.remove(fp.name)

    def _download(self) -> str:
        assert self._cache_dir
        os.makedirs(self._cache_dir, exist_ok=True)
        dest = os.path.join(self._cache_dir, self._filename)

        response = self._get_request()
        # check to see if we have a file which matches the connection
        # only download if we do not (cache miss, vs hit)
        if not self._cache_hit(dest, response):
            self._write(dest, response)

        return dest

    @contextlib.contextmanager
    def open(self) -> t.Generator[t.BinaryIO, None, None]:
        if (not self._cache_dir) or self._disable_cache:
            yield io.BytesIO(self._get_request().content)
        else:
            with open(self._download(), "rb") as fp:
                yield fp
