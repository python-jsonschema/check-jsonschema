import os
import pathlib
import sys

import pytest
import responses


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
