import contextlib
import os
import platform
import shutil
import tempfile
import time
import typing as t
import urllib.request


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
        filename: t.Optional[str] = None,
        cache_dir: t.Optional[str] = None,
        disable_cache: bool = False,
    ):
        self._file_url = file_url
        self._filename = filename or file_url.split("/")[-1]
        self._cache_dir = cache_dir or self._compute_default_cache_dir()
        self._disable_cache = disable_cache

    def _compute_default_cache_dir(self) -> t.Optional[str]:
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

    def _lastmod_from_conn(self, conn) -> float:
        return time.mktime(
            time.strptime(
                conn.headers.get("last-modified", self._LASTMOD_DEFAULT),
                self._LASTMOD_FMT,
            )
        )

    def _cache_hit(self, cachefile, conn):
        # if caching is disabled, "turn off" any cache hits
        if self.disable_cache:
            return False

        # no file? miss
        if not os.path.exists(cachefile):
            return False

        # compare mtime on any cached file against the remote last-modified time
        local_mtime = os.path.getmtime(cachefile)
        remote_mtime = self._lastmod_from_conn(conn)
        return local_mtime < remote_mtime

    @contextlib.contextmanager
    def _urlopen(self):
        with urllib.request.urlopen(self._file_url) as conn:
            yield conn

    def _write(self, conn, dest):
        # download to a temp file and then move to the dest
        # this makes the download safe if run in parallel (parallel runs
        # won't create a new empty file for writing and cause failures)
        fp = tempfile.NamedTemporaryFile(mode="wb", delete=False)
        fp.write(conn.read())
        fp.close()
        shutil.copy(fp.name, dest)
        os.remove(fp.name)

    def _download(self):
        os.makedirs(self._cache_dir, exist_ok=True)
        dest = os.path.join(self._cache_dir, self._filename)

        with self._urlopen() as conn:
            # check to see if we have a file which matches the connection
            # only download if we do not (cache miss, vs hit)
            if not self._cache_hit(dest, conn):
                self._write(conn, dest)

        return dest

    @contextlib.contextmanager
    def open(self):
        if not self._cache_dir:
            with urllib.request.urlopen(self._file_url) as fp:
                yield fp
        else:
            cached_file = self._download()
            with open(cached_file, "r") as fp:
                yield fp
