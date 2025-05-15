import inspect
import os
import pathlib
import sys

import pytest
import responses
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    # compatibility for click==8.2.0 vs click<=8.1
    sig = inspect.signature(CliRunner)
    if "mix_stderr" in sig.parameters:
        return CliRunner(mix_stderr=False)
    return CliRunner()


@pytest.fixture(autouse=True)
def mocked_responses():
    responses.start()
    yield
    responses.stop()
    responses.reset()


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
def url2cachepath():
    from check_jsonschema.cachedownloader import url_to_cache_filename

    def _get(cache_dir, url):
        return cache_dir / url_to_cache_filename(url)

    return _get


@pytest.fixture
def downloads_cache_dir(tmp_path):
    return tmp_path / ".cache" / "check_jsonschema" / "downloads"


@pytest.fixture
def get_download_cache_loc(downloads_cache_dir, url2cachepath):
    def _get(url):
        return url2cachepath(downloads_cache_dir, url)

    return _get


@pytest.fixture
def inject_cached_download(downloads_cache_dir, get_download_cache_loc):
    def _write(uri, content):
        downloads_cache_dir.mkdir(parents=True)
        path = get_download_cache_loc(uri)
        if isinstance(content, str):
            path.write_text(content)
        else:
            path.write_bytes(content)

    return _write


@pytest.fixture
def refs_cache_dir(tmp_path):
    return tmp_path / ".cache" / "check_jsonschema" / "refs"


@pytest.fixture
def get_ref_cache_loc(refs_cache_dir, url2cachepath):
    def _get(url):
        return url2cachepath(refs_cache_dir, url)

    return _get


@pytest.fixture
def inject_cached_ref(refs_cache_dir, get_ref_cache_loc):
    def _write(uri, content):
        refs_cache_dir.mkdir(parents=True)
        get_ref_cache_loc(uri).write_text(content)

    return _write
