from __future__ import annotations

import contextlib
import functools
import io
import logging
import os
import platform
import typing as t

import cachecontrol
import requests
from cachecontrol.caches.file_cache import FileCache

log = logging.getLogger(__name__)


def _base_cache_dir() -> str | None:
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

    return cache_dir


def _resolve_cache_dir(dirname: str) -> str | None:
    cache_dir = _base_cache_dir()
    if cache_dir:
        cache_dir = os.path.join(cache_dir, "check_jsonschema", dirname)
    return cache_dir


def _get_request(
    session: requests.Session,
    file_url: str,
    *,
    response_ok: t.Callable[[requests.Response], bool],
) -> requests.Response:
    num_retries = 2
    r: requests.Response | None = None
    for _attempt in range(num_retries + 1):
        try:
            # On retries, bypass CacheControl's local cache to avoid
            # re-serving a cached bad response. Ideally we'd delete the
            # cache entry directly, but CacheControl doesn't expose a public
            # API for this (see https://github.com/psf/cachecontrol/issues/219).
            # The no-cache header forces revalidation with the origin server.
            headers = {"Cache-Control": "no-cache"} if _attempt > 0 else {}
            r = session.get(file_url, headers=headers)
        except requests.RequestException as e:
            if _attempt == num_retries:
                raise FailedDownloadError("encountered error during download") from e
            continue
        if r.ok and response_ok(r):
            return r
    assert r is not None
    raise FailedDownloadError(
        f"got response with status={r.status_code}, retries exhausted"
    )


class FailedDownloadError(Exception):
    pass


class CacheDownloader:
    def __init__(self, cache_dir: str, *, disable_cache: bool = False) -> None:
        self._cache_dir = _resolve_cache_dir(cache_dir)
        self._disable_cache = disable_cache

    @functools.cached_property
    def _session(self) -> requests.Session:
        session = requests.Session()
        if self._cache_dir and not self._disable_cache:
            log.debug("using cache dir: %s", self._cache_dir)
            os.makedirs(self._cache_dir, exist_ok=True)
            session = cachecontrol.CacheControl(
                session, cache=FileCache(self._cache_dir)
            )
        else:
            log.debug("caching disabled")
        return session

    @contextlib.contextmanager
    def open(
        self,
        file_url: str,
        validate_response: t.Callable[[requests.Response], bool],
    ) -> t.Iterator[t.IO[bytes]]:
        response = _get_request(self._session, file_url, response_ok=validate_response)
        yield io.BytesIO(response.content)

    def bind(
        self,
        file_url: str,
        validation_callback: t.Callable[[bytes], t.Any] | None = None,
    ) -> BoundCacheDownloader:
        return BoundCacheDownloader(
            file_url, self, validation_callback=validation_callback
        )


class BoundCacheDownloader:
    def __init__(
        self,
        file_url: str,
        downloader: CacheDownloader,
        *,
        validation_callback: t.Callable[[bytes], t.Any] | None = None,
    ) -> None:
        self._file_url = file_url
        self._downloader = downloader
        self._validation_callback = validation_callback

    @contextlib.contextmanager
    def open(self) -> t.Iterator[t.IO[bytes]]:
        with self._downloader.open(
            self._file_url,
            validate_response=self._validate_response,
        ) as fp:
            yield fp

    def _validate_response(self, response: requests.Response) -> bool:
        if not self._validation_callback:
            return True
        # CacheControl sets from_cache=True on cache hits; skip re-validation.
        # Plain requests.Session (used when disable_cache=True) doesn't set this
        # attribute at all, so we use getattr with a default.
        if getattr(response, "from_cache", False):
            return True
        try:
            self._validation_callback(response.content)
            return True
        except ValueError:
            return False
