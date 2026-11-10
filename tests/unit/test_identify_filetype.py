import pathlib

import pytest

from check_jsonschema.identify_filetype import path_to_type


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("foo.json", "json"),
        ("foo.yaml", "yaml"),
        ("foo.yml", "yaml"),
        ("foo.toml", "toml"),
        ("foo.JSON", "json"),
        ("foo.YAML", "yaml"),
        ("foo.YML", "yaml"),
        ("foo.TOML", "toml"),
    ],
)
def test_path_to_type_matches_known_extensions(filename, expected):
    assert path_to_type(filename) == expected


@pytest.mark.parametrize(
    "filename",
    ["foo.JSON", "foo.YAML", "foo.TOML"],
)
def test_path_to_type_matches_known_extensions_pathlib(filename):
    assert path_to_type(pathlib.Path(filename)) == path_to_type(filename)


def test_path_to_type_unknown_extension_uses_default():
    assert path_to_type("foo.odt") == "json"
    assert path_to_type("foo.ODT") == "json"


def test_path_to_type_uppercase_json_beats_non_json_default():
    assert path_to_type("foo.JSON", default_type="yaml") == "json"
