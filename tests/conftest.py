import inspect
import io
import os
import pathlib
import sys
from email.utils import formatdate

import pytest
import responses
from click.testing import CliRunner


class _CacheControlCompatibleBytesIO(io.BytesIO):
    """A BytesIO that signals closed to cachecontrol after all data is read.

    cachecontrol's CallbackFileWrapper checks `fp.fp is None` to determine
    if the response has been fully read. Standard BytesIO doesn't have an
    `fp` attribute, so cachecontrol falls back to checking `fp.closed`,
    which only returns True after explicit `.close()`. This class adds
    an `fp` property that returns None after all data has been read,
    allowing cachecontrol to properly cache responses from the `responses`
    mock library.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._fully_read = False

    @property
    def fp(self):
        return None if self._fully_read else self

    def read(self, size=-1):
        data = super().read(size)
        if self.tell() == len(self.getvalue()):
            self._fully_read = True
        return data


@pytest.fixture
def cli_runner():
    # compatibility for click==8.2.0 vs click<=8.1
    sig = inspect.signature(CliRunner)
    if "mix_stderr" in sig.parameters:
        return CliRunner(mix_stderr=False)
    return CliRunner()


@pytest.fixture(autouse=True)
def mocked_responses():
    # Patch responses._handle_body to return a BytesIO subclass that properly
    # signals "closed" to cachecontrol, enabling HTTP caching in tests.
    original_handle_body = responses._handle_body

    def _patched_handle_body(body):
        result = original_handle_body(body)
        if isinstance(result, io.BytesIO):
            return _CacheControlCompatibleBytesIO(result.getvalue())
        return result

    responses._handle_body = _patched_handle_body
    responses.start()
    yield
    responses.stop()
    responses.reset()
    responses._handle_body = original_handle_body


@pytest.fixture
def mock_module(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(tmp_path)
    all_names_to_clear = []

    def func(path, text):
        path = pathlib.Path(path)
        mod_dir = tmp_path / path.parent
        mod_dir.mkdir(parents=True, exist_ok=True)
        for part in path.parts[:-1]:
            (tmp_path / part / "__init__.py").touch()

        (tmp_path / path).write_text(text)

        for i in range(len(path.parts)):
            modname = ".".join(path.parts[: i + 1])
            if modname.endswith(".py"):
                modname = modname[:-3]
            all_names_to_clear.append(modname)

    yield func

    for name in all_names_to_clear:
        if name in sys.modules:
            del sys.modules[name]


@pytest.fixture
def in_tmp_dir(request, tmp_path):
    os.chdir(str(tmp_path))
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture
def cache_dir(tmp_path):
    return tmp_path / ".cache"


@pytest.fixture(autouse=True)
def patch_cache_dir(monkeypatch, cache_dir):
    with monkeypatch.context() as m:
        m.setattr(
            "check_jsonschema.cachedownloader._base_cache_dir", lambda: str(cache_dir)
        )
        yield m


@pytest.fixture
def schemas_cache_dir(tmp_path):
    return tmp_path / ".cache" / "check_jsonschema" / "schemas"


@pytest.fixture
def refs_cache_dir(tmp_path):
    return tmp_path / ".cache" / "check_jsonschema" / "refs"


# Alias for unit tests that use "downloads" as the cache dir name
@pytest.fixture
def downloads_cache_dir(tmp_path):
    return tmp_path / ".cache" / "check_jsonschema" / "downloads"


@pytest.fixture
def cacheable_headers():
    """Returns HTTP headers that enable cachecontrol caching."""
    return {
        "Cache-Control": "max-age=31536000",
        "Date": formatdate(usegmt=True),
    }
