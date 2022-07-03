import os

import pytest

from check_jsonschema.instance_loader import InstanceLoader
from check_jsonschema.parsers import BadFileTypeError
from check_jsonschema.parsers.json5 import ENABLED as JSON5_ENABLED
from check_jsonschema.parsers.toml import ENABLED as TOML_ENABLED


@pytest.fixture
def in_tmp_dir(request, tmp_path):
    os.chdir(str(tmp_path))
    yield
    os.chdir(request.config.invocation_dir)


@pytest.mark.parametrize(
    "filename, default_ft",
    [
        ("foo.json", None),
        ("foo.json", "json"),
        ("foo.json", "yaml"),
        ("foo", "json"),
        # YAML is a superset of JSON, so using the YAML loader should be safe when the
        # data is JSON
        ("foo", "yaml"),
    ],
)
def test_instanceloader_json_data(tmp_path, filename, default_ft):
    f = tmp_path / filename
    f.write_text("{}")
    loader = InstanceLoader([str(f)], default_filetype=default_ft)
    data = list(loader.iter_files())
    assert data == [(str(f), {})]


@pytest.mark.parametrize(
    "filename, default_ft",
    [
        ("foo.yaml", None),
        ("foo.yml", None),
        ("foo.yaml", "json"),
        ("foo.yml", "json"),
        ("foo.yaml", "yaml"),
        ("foo.yml", "yaml"),
        ("foo", "yaml"),
    ],
)
def test_instanceloader_yaml_data(tmp_path, filename, default_ft):
    f = tmp_path / filename
    f.write_text(
        """\
a:
  b:
   - 1
   - 2
  c: d
"""
    )
    loader = InstanceLoader([str(f)], default_filetype=default_ft)
    data = list(loader.iter_files())
    assert data == [(str(f), {"a": {"b": [1, 2], "c": "d"}})]


def test_instanceloader_unknown_type(tmp_path):
    f = tmp_path / "foo"  # no extension here
    f.write_text("{}")  # json data (could be detected as either)
    loader = InstanceLoader([str(f)])
    # at iteration time, the file should error
    with pytest.raises(BadFileTypeError):
        list(loader.iter_files())


@pytest.mark.parametrize(
    "enabled_flag, extension, file_content, expect_data, expect_error_message",
    [
        (
            JSON5_ENABLED,
            "json5",
            "{}",
            {},
            "pip install json5",
        ),
        (
            TOML_ENABLED,
            "toml",
            '[foo]\nbar = "baz"\n',
            {"foo": {"bar": "baz"}},
            "pip install tomli",
        ),
    ],
)
def test_instanceloader_optional_format_handling(
    tmp_path, enabled_flag, extension, file_content, expect_data, expect_error_message
):
    f = tmp_path / f"foo.{extension}"
    f.write_text(file_content)
    loader = InstanceLoader([str(f)])
    if enabled_flag:
        # at iteration time, the file should load fine
        data = list(loader.iter_files())
        assert data == [(str(f), expect_data)]
    else:
        # at iteration time, an error should be raised
        with pytest.raises(BadFileTypeError) as excinfo:
            list(loader.iter_files())

        err = excinfo.value
        # error message should be instructive
        assert expect_error_message in str(err)
