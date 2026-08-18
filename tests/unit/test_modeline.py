import pytest

from check_jsonschema.modeline import (
    extract_yaml_modeline_schema,
    resolve_modeline_schema_location,
)


@pytest.mark.parametrize(
    "line",
    [
        "# yaml-language-server: $schema=https://example.com/schema.json",
        "  # yaml-language-server :   $schema = https://example.com/schema.json",
        "# yaml-language-server: $schema: https://example.com/schema.json",
        "# $schema=https://example.com/schema.json",
        "# $schema: https://example.com/schema.json",
    ],
)
def test_extract_yaml_modeline_schema_supported_forms(line):
    data = f"---\n{line}\nfoo: bar\n".encode()
    assert extract_yaml_modeline_schema(data) == "https://example.com/schema.json"


def test_extract_yaml_modeline_schema_returns_first_match():
    data = b"""\
# yaml-language-server: $schema=https://example.com/first.json
# yaml-language-server: $schema=https://example.com/second.json
"""
    assert extract_yaml_modeline_schema(data) == "https://example.com/first.json"


def test_extract_yaml_modeline_schema_requires_full_line_comment():
    assert (
        extract_yaml_modeline_schema(
            b"foo: bar  # yaml-language-server: $schema=https://example.com/schema.json"
        )
        is None
    )


def test_resolve_modeline_schema_location_relative_to_instance(tmp_path):
    instance = tmp_path / "configs" / "foo.yaml"
    instance.parent.mkdir()
    instance.write_text("")

    schema_location = resolve_modeline_schema_location(
        "../schemas/foo.json", str(instance)
    )

    assert schema_location == str(tmp_path / "schemas" / "foo.json")


def test_resolve_modeline_schema_location_remote_unchanged():
    assert (
        resolve_modeline_schema_location("https://example.com/schema.json", "foo.yaml")
        == "https://example.com/schema.json"
    )


def test_resolve_modeline_schema_location_relative_stdin_fails():
    with pytest.raises(ValueError, match="cannot be resolved for stdin"):
        resolve_modeline_schema_location("schemas/foo.json", "-")
