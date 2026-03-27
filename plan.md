# Plan: Replace Custom Cache with CacheControl

Fixes https://github.com/python-jsonschema/check-jsonschema/issues/668

## Problem

The current cache implementation in `cachedownloader.py` uses only the
`Last-Modified` header for cache validation. When a server omits that header
(but provides `ETag` or `Cache-Control`), `_lastmod_from_response()` returns
`0.0` and `_cache_hit()` always returns `True`, so the cache never invalidates.

## Solution

Replace the hand-rolled mtime-based cache logic with the
[CacheControl](https://github.com/psf/cachecontrol) library (v0.14, maintained
under the PSF). CacheControl wraps a `requests.Session` and implements full HTTP
caching semantics — `ETag`/`If-None-Match`, `Last-Modified`/`If-Modified-Since`,
and `Cache-Control` headers — transparently. On-disk persistence uses its
`FileCache` backend (backed by `filelock` for concurrency safety).

## Behavior Changes

| Aspect | Before | After |
|---|---|---|
| ETag support | None | Full (`If-None-Match` / 304) |
| `Cache-Control` header | Ignored | Respected (`max-age`, `no-cache`, `no-store`) |
| `Last-Modified` | Only mechanism (buggy when absent) | Supported via `If-Modified-Since` / 304 |
| No caching headers at all | Cache never invalidates (bug) | Not cached — see note below |
| Existing cache files on upgrade | Used | Ignored (incompatible format) — see open question below |
| Cache file format | Raw content, SHA-256 filename | CacheControl msgpack-serialized HTTP response, SHA-224 filename in 5-level dir tree |
| `--no-cache` flag | Unchanged | Unchanged — plain session, no caching |
| Retry on error / bad data | Unchanged | Unchanged — custom retry loop preserved |
| Concurrency safety | `_atomic_write` (tempfile + shutil.copy) | `filelock` (via `FileCache`) |

### Servers with no caching headers

When a server provides no caching headers at all (no `ETag`, no `Last-Modified`,
no `Cache-Control`, no `Expires`), the current code caches the response forever
due to the `_lastmod_from_response` returning `0.0` bug. After this change, such
responses will not be cached, following correct HTTP semantics. In practice,
nearly all real-world schema endpoints provide at least one caching header.

CacheControl has built-in heuristic support for overriding this behavior if
needed. The `ExpiresAfter` heuristic (bundled, not custom) can apply a TTL to all
responses. For a conditional variant that only applies to responses lacking
server-provided caching headers, the documented `BaseHeuristic` extensibility
point allows a small subclass (~10 lines). Neither is a hack — heuristics are a
first-class CacheControl feature designed for exactly this purpose, and
[RFC 7234](https://tools.ietf.org/html/rfc7234) explicitly permits caching
systems to use heuristics for responses that lack caching headers.

### Open question: clean up old cache files?

CacheControl uses the same cache directories (`check_jsonschema/schemas/`,
`check_jsonschema/refs/`) but a different file layout (5-level SHA-224 tree vs.
flat SHA-256 files). Old cache files will sit alongside the new CacheControl
tree, ignored but taking up space.

Options:
1. **Do nothing** (current default) — old files are harmless. Users can manually
   delete the cache directory if they want to reclaim space.
2. **Delete on first run** — on `_build_session()`, detect and remove files
   matching the old naming pattern (64-char hex + optional extension, no
   subdirectories). Risk: could delete user files if they happen to match.
3. **One-time migration warning** — log a message suggesting users clear their
   cache directory. Non-invasive but adds noise.

**Proceeding with option 1 (do nothing) unless revisited.**

---

## 1. Dependency Changes

**File: `pyproject.toml`** (line 39-46)

Add `CacheControl[filecache]` to runtime dependencies:

```toml
dependencies = [
    'tomli>=2.0;python_version<"3.11"',
    "ruamel.yaml>=0.18.10,<0.20.0",
    "jsonschema>=4.18.0,<5.0",
    "regress>=2024.11.1",
    "requests<3.0",
    "click>=8,<9",
    "CacheControl[filecache]>=0.14,<0.15",
]
```

The `[filecache]` extra pulls in `filelock`. CacheControl also depends on
`msgpack` (for response serialization) and `requests` (already a dependency).

---

## 2. Rewrite `src/check_jsonschema/cachedownloader.py`

### Remove

| Symbol | Lines | Reason |
|---|---|---|
| `_LASTMOD_FMT` | 16 | CacheControl handles Last-Modified natively |
| `_lastmod_from_response()` | 45-54 | Same |
| `_cache_hit()` | 88-97 | CacheControl handles freshness and conditional requests |
| `_atomic_write()` | 77-85 | FileCache uses `filelock` for concurrency |

### Preserve existing imports

`from __future__ import annotations` (line 1) stays. `hashlib` stays (used by
`url_to_cache_filename`). `platform` stays (used by `_base_cache_dir`).

### Remove imports no longer needed

`calendar`, `shutil`, `tempfile`, `time` — verify each is truly unused after
the rewrite.

### Add imports (top-level, third-party group)

```python
import cachecontrol
from cachecontrol.caches.file_cache import FileCache
```

These go in the third-party import group alongside `import requests`, following
the project's PEP 8 / isort convention (no lazy imports in production code).

### Keep unchanged

| Symbol | Lines | Reason |
|---|---|---|
| `_base_cache_dir()` | 19-35 | Still needed for platform-specific cache path |
| `_resolve_cache_dir()` | 38-42 | Still needed |
| `url_to_cache_filename()` | 100-116 | Useful utility; not used by CacheControl but no reason to remove |
| `FailedDownloadError` | 119-120 | Still raised by retry logic |

### Modify `_get_request()` (lines 57-74)

- Add `session: requests.Session` as the first parameter.
- Call `session.get(file_url)` instead of `requests.get(file_url, stream=True)`.
- Remove `stream=True` — CacheControl needs the full response to cache it, and
  schemas are small.
- Keep the retry loop (2 retries) and `response_ok` callback — CacheControl does
  not provide retry logic.

**Retry / CacheControl interaction:** When a server returns a 200 with corrupt
body *and* caching headers (e.g., ETag), CacheControl caches the response before
our `response_ok` callback runs. On a naive retry, `session.get()` would serve
the cached corrupt response and every retry would fail identically. To avoid
this, retry attempts (`_attempt > 0`) pass `Cache-Control: no-cache` in the
request headers. This is standard HTTP (RFC 7234 §5.2.1.4) — it tells
CacheControl to revalidate with the server rather than serve from its local
cache. CacheControl implements this natively; no custom logic is needed.

```python
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
            # re-serving a cached bad response.
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
```

### Rewrite `CacheDownloader` (lines 123-180)

- `__init__`: store config only. Do **not** build the session eagerly —
  `test_default_cache_dir` creates `CacheDownloader` with fake/relative cache
  paths purely to assert `_cache_dir` resolution and never makes HTTP requests.
  Eager `os.makedirs` + `FileCache()` in `__init__` would create real
  directories using those fake paths.
- Build the session lazily via a `_session` property on first access (i.e.,
  first `open()` call). This also avoids creating sessions that are never used
  (e.g., if the schema turns out to be local after all).
- Remove `_download()` entirely — CacheControl manages on-disk cache files.
- Simplify `open()` — always yields `io.BytesIO(response.content)`. No
  branching needed: when cache is enabled, `self._session` is a
  CacheControl-wrapped session (handles caching transparently); when disabled,
  it is a plain `Session`.
- `bind()` — unchanged API.

CacheControl imports go at the **top of the module** alongside `requests`,
following the project convention (no lazy/deferred imports in production code):

```python
import cachecontrol
from cachecontrol.caches.file_cache import FileCache
```

```python
class CacheDownloader:
    def __init__(self, cache_dir: str, *, disable_cache: bool = False) -> None:
        self._cache_dir = _resolve_cache_dir(cache_dir)
        self._disable_cache = disable_cache
        self._cached_session: requests.Session | None = None

    @property
    def _session(self) -> requests.Session:
        if self._cached_session is None:
            self._cached_session = self._build_session()
        return self._cached_session

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        if self._cache_dir and not self._disable_cache:
            os.makedirs(self._cache_dir, exist_ok=True)
            session = cachecontrol.CacheControl(
                session, cache=FileCache(self._cache_dir)
            )
        return session

    @contextlib.contextmanager
    def open(
        self,
        file_url: str,
        filename: str,
        validate_response: t.Callable[[requests.Response], bool],
    ) -> t.Iterator[t.IO[bytes]]:
        response = _get_request(
            self._session, file_url, response_ok=validate_response
        )
        yield io.BytesIO(response.content)

    def bind(
        self,
        file_url: str,
        filename: str | None = None,
        validation_callback: t.Callable[[bytes], t.Any] | None = None,
    ) -> BoundCacheDownloader:
        return BoundCacheDownloader(
            file_url, self, filename=filename,
            validation_callback=validation_callback,
        )
```

The `filename` parameter in `open()` and `bind()` is kept for API compatibility
but ignored — CacheControl manages its own filenames (SHA-224 hash of normalized
URL in a 5-level directory tree).

`BoundCacheDownloader.__init__` still computes `self._filename = filename or
url_to_cache_filename(file_url)` (line 193). This is now dead code — the value
is passed through to `CacheDownloader.open()` which ignores it. Kept for now
since `test_default_filename_from_uri` asserts on `cd._filename`. Can be cleaned
up in a follow-up.

### Modify `BoundCacheDownloader._validate_response()` (lines 206-213)

Skip validation on cache hits. CacheControl sets `response.from_cache = True` on
every response served from cache (either a direct hit or after a 304
revalidation). This preserves the fix for
[#453](https://github.com/python-jsonschema/check-jsonschema/issues/453)
(validation callback must not run on cache hits).

```python
def _validate_response(self, response: requests.Response) -> bool:
    if not self._validation_callback:
        return True
    # CacheControl sets from_cache=True on cache hits; skip re-validation
    if getattr(response, "from_cache", False):
        return True
    try:
        self._validation_callback(response.content)
        return True
    except ValueError:
        return False
```

---

## 3. Changes to Callers

**No changes** to `readers.py` or `resolver.py`. Both use `CacheDownloader` via
`bind()` and `open()`, whose signatures are unchanged.

- `readers.py:80` — `CacheDownloader("schemas", disable_cache=...).bind(url, validation_callback=...)`
- `resolver.py:53` — `CacheDownloader("refs", disable_cache=...)`

Cache subdirectory names (`"schemas"`, `"refs"`) are preserved.

**Update `cli/main_command.py:96`**: The `--schemafile` help text says schemas
will be `"downloaded and cached locally based on mtime."` Replace with generic
wording (e.g., `"downloaded and cached locally"`) since caching is no longer
mtime-based.

---

## 4. Test Changes

### Test strategy: trust CacheControl, test integration only

CacheControl's `FileCache` write mechanism relies on a `CallbackFileWrapper`
that monitors when a response stream is fully consumed. The `responses` mock
library creates `BytesIO` bodies that never report `.closed = True` after
exhaustion, so the cache-write callback never fires. **CacheControl never
populates its FileCache when responses come from `responses` mocks.**

This means tests cannot verify CacheControl's caching behavior (cache hits,
ETag revalidation, max-age expiry) using `responses`. Rather than switching test
infrastructure (e.g., adding a real HTTP server), the test strategy is:

- **Trust CacheControl** for caching correctness — it is a well-maintained PSF
  project with its own test suite.
- **Test our integration**: retry logic, validation callbacks, `--no-cache` flag,
  session construction, error handling.
- **Do not assert** on cache file existence, `response.from_cache`, or
  `len(responses.calls)` staying constant across requests.

### `responses` library compatibility

The `responses` library (v0.26.0) patches `HTTPAdapter.send` at the class level.
CacheControl's `CacheControlAdapter` calls `super().send()`, which hits the
`responses` mock. HTTP request/response flow works normally — only the cache-write
side effect is broken. Tests that use `responses` for mocking HTTP (retry tests,
validation tests, error tests) work fine.

### `tests/conftest.py` — Fixture changes

**Update `patch_cache_dir`** (line 67): Works as-is — it monkeypatches
`_base_cache_dir`, which is still called by `_resolve_cache_dir`, which is still
called by `CacheDownloader.__init__`. CacheControl's `FileCache` will use the
patched temp directory.

**Remove the following fixtures** — they either inject raw cache files (no longer
valid format) or predict cache file paths using `url_to_cache_filename`
(SHA-256), which CacheControl does not use:

| Fixture | Line | Action |
|---|---|---|
| `url2cachepath` | 77 | Remove — only consumed by the path-prediction fixtures below |
| `inject_cached_download` | 100 | Remove — writes raw content; CacheControl uses msgpack format |
| `inject_cached_ref` | 126 | Remove — same |
| `get_download_cache_loc` | 92 | Remove — path prediction no longer valid |
| `get_ref_cache_loc` | 118 | Remove — same |

**Keep `downloads_cache_dir` / `refs_cache_dir`** (lines 87, 113) and
**keep `cache_dir`** (line 63) — still useful for asserting cache directory
existence when needed.

### `tests/unit/test_cachedownloader.py` — Specific changes

**Update the import block** (lines 10-16): Remove `_cache_hit` and
`_lastmod_from_response` — both symbols are deleted from `cachedownloader.py`.

**Tests to remove:**

| Test | Lines | Reason |
|---|---|---|
| `test_cache_hit_by_mtime` | 95-113 | mtime-based caching removed entirely |
| `test_cachedownloader_handles_bad_lastmod_header` | 257-310 | `_lastmod_from_response` removed |
| `test_lastmod_from_header_uses_gmtime` | 352-383 | Same |
| `test_cachedownloader_cached_file` | 116-129 | Tests monkeypatched `_download` method, which is removed |
| `test_cachedownloader_validation_is_not_invoked_on_hit` | 313-345 | Depends on `inject_cached_download` (removed) and `response.from_cache` (not testable with `responses` mocks) |

**Tests to simplify** (remove `get_download_cache_loc` dependency and file-
existence assertions — these tests are about retry behavior, not caching):

`test_cachedownloader_on_success` (line 132):
- Remove `get_download_cache_loc` fixture usage and `f.exists()` assertions.
- Keep: verify `cd.open()` returns correct content (`b"{}"`).

`test_cachedownloader_succeeds_after_few_errors` (line 160):
- Remove `get_download_cache_loc` fixture usage and `f.exists()` assertions.
- Keep: verify `cd.open()` returns correct content after retries.

`test_cachedownloader_fails_after_many_errors` (line 194):
- Remove `get_download_cache_loc` fixture usage and `f.exists()` assertion.
- Keep: verify `FailedDownloadError` is raised.

`test_cachedownloader_retries_on_bad_data` (line 225):
- Remove `get_download_cache_loc` fixture usage and `f.exists()` assertions.
- Keep: verify `cd.open()` returns correct content after retrying past bad data.

`test_cachedownloader_using_alternate_target_dir` (line 149):
- Remove `url2cachepath` / path-based assertions.
- Keep: verify `cd.open()` returns correct content.

**Tests to keep as-is:**

| Test | Lines | Notes |
|---|---|---|
| `test_default_filename_from_uri` | 37-39 | `url_to_cache_filename` unchanged |
| `test_default_cache_dir` | 42-92 | `_base_cache_dir` unchanged. Works as-is thanks to lazy session building — `CacheDownloader("downloads")` only stores `_cache_dir`, no `os.makedirs` or `FileCache` until `open()` is called. |

**New tests to add (integration-focused):**

| Test | Purpose |
|---|---|
| `test_disable_cache_uses_plain_session` | When `disable_cache=True`, verify `_build_session` returns a plain `requests.Session` (not wrapped by CacheControl). |
| `test_enable_cache_uses_cachecontrol_session` | When `disable_cache=False` and cache dir is valid, verify `_build_session` returns a CacheControl-wrapped session (check for `CacheControlAdapter` on the session). |
| `test_cache_dir_none_uses_plain_session` | When `_resolve_cache_dir` returns `None` (e.g., Windows with no env vars), verify `_build_session` returns a plain session. |

**Aspirational cache-behavior tests** (require a real HTTP server or alternative
to `responses`; not included in this PR but tracked for follow-up):

| Test | Purpose |
|---|---|
| `test_etag_cache_revalidation` | Server provides `ETag`, no `Last-Modified`. Second request sends `If-None-Match`, gets 304. |
| `test_cache_control_max_age` | Server provides `Cache-Control: max-age=3600`. Second request served from cache. |
| `test_last_modified_revalidation` | Server provides `Last-Modified`. Second request sends `If-Modified-Since`. |
| `test_no_caching_headers_not_cached` | Server provides no caching headers. Response is not cached. |

### `tests/acceptance/test_remote_ref_resolution.py`

`test_remote_ref_resolution_cache_control` (line 68):
- Remove `get_ref_cache_loc` fixture dependency and file-path assertions.
- When `disable_cache=False`: verify the command succeeds (exit code 0).
  Cache behavior is trusted to CacheControl.
- When `disable_cache=True`: verify the command succeeds (exit code 0).

`test_remote_ref_resolution_loads_from_cache` (line 105):
- Remove `inject_cached_ref` and `get_ref_cache_loc` fixture dependencies.
- This test's premise (inject good cache data, serve bad HTTP, verify cache is
  used) cannot be replicated without direct FileCache manipulation. **Remove
  this test.** Cache-hit behavior is trusted to CacheControl.

`test_remote_ref_resolution_callout_count_is_scale_free_in_instancefiles`
(line 251):
- Should work as-is. Within-run deduplication is handled by `lru_cache` on
  `_get_validator` and the in-memory `ResourceCache` — not by the file cache.
  CacheControl's file cache only affects cross-run persistence.

### `tests/acceptance/test_nonjson_schema_handling.py`

`test_can_load_remote_yaml_schema_ref_from_cache` (line 140):
- Remove `inject_cached_ref` fixture dependency. This test's premise (inject
  good cache, serve bad HTTP) cannot be replicated. **Remove this test.**
  Cache-hit behavior is trusted to CacheControl.

---

## 5. Pytest Warning Filter

CacheControl's `FileCache` uses `filelock` for concurrency safety. When connection
errors occur during tests (e.g., `test_cachedownloader_fails_after_many_errors`),
filelock may leave temporary files open, triggering a `ResourceWarning` that pytest
converts to `PytestUnraisableExceptionWarning`.

This is not a bug in our code — it's a side effect of how filelock handles error
conditions. Add a filter to `pyproject.toml` to ignore this specific warning:

```toml
[tool.pytest.ini_options]
filterwarnings = [
    # ... existing filters ...
    # filelock (used by CacheControl) may leave temp files open during connection errors
    'ignore:Exception ignored in.*FileIO.*:pytest.PytestUnraisableExceptionWarning',
]
```

**TODO:** Investigate whether this warning can be avoided rather than suppressed.

**Investigation results (2026-03-27):**
- The warning originates from CacheControl's `CallbackFileWrapper` class in
  `filewrapper.py`, not filelock.
- `CallbackFileWrapper.__init__` creates a `NamedTemporaryFile` (line 37), which
  is only closed in `_close()` when the response is fully read (line 105-106).
- When a `requests.ConnectionError` occurs, the temp file is never closed because
  `_close()` is never called.
- No existing upstream issues found in CacheControl or filelock for this specific
  problem.
- The `CallbackFileWrapper` class lacks a `__del__` method or context manager
  protocol that would ensure cleanup on exceptions.
- **Recommendation:** File an upstream issue with CacheControl suggesting that
  `CallbackFileWrapper` implement `__del__` to close `self.__buf` if not already
  closed, or use a weak reference callback to ensure cleanup.

---

## 6. Execution Order

1. Add `CacheControl[filecache]` dependency to `pyproject.toml`
2. Rewrite `cachedownloader.py`
3. Update `conftest.py` fixtures
4. Rewrite/update unit tests in `test_cachedownloader.py`
5. Update acceptance tests
6. Add pytest warning filter for filelock ResourceWarning
7. Run full test suite, fix any `responses` library compatibility issues
8. Commit, push, open PR
