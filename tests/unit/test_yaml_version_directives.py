import codecs
import io
from unittest.mock import Mock

import pytest

from check_jsonschema.parsers import FailedFileLoadError, ParserSet, yaml


@pytest.mark.parametrize(
    "encoding,bom",
    [
        ("utf-8", b""),
        ("utf-8-sig", b""),
        ("utf-16", b""),
        ("utf-16-be", codecs.BOM_UTF16_BE),
    ],
)
@pytest.mark.parametrize(
    "preamble",
    [
        "",
        "# configuration\n\n",
        "%TAG !e! tag:example.com,2026:\n",
        "\r\n# comment\r\n",
    ],
)
@pytest.mark.parametrize("version", ["1.1", "1.01", "01.1"])
def test_yaml_11_directive_uses_version_aware_parser(encoding, bom, preamble, version):
    primary = yaml.construct_yaml_implementation()
    fallback = yaml.construct_yaml_implementation(pure=True)
    # Reproduce the C parser's result even when that optional backend is absent.
    primary.load = Mock(return_value="on")
    load = yaml.impl2loader(primary, fallback)
    data = bom + f"{preamble}%YAML {version} # explicit version\n---\non\n".encode(
        encoding
    )

    assert load(io.BytesIO(data)) is True


@pytest.mark.parametrize(
    "data",
    [
        b"on\n",
        b"%YAML 1.2\n---\non\n",
        b"# %YAML 1.1\non\n",
        b"value: |\n  %YAML 1.1\nother: on\n",
        b'"before\n%YAML 1.1\nafter"\n',
    ],
)
def test_other_yaml_keeps_the_primary_parser(data):
    primary = yaml.construct_yaml_implementation()
    fallback = yaml.construct_yaml_implementation(pure=True)
    primary.load = Mock(return_value="primary")
    fallback.load = Mock(side_effect=AssertionError("unexpected fallback"))

    assert yaml.impl2loader(primary, fallback)(io.BytesIO(data)) == "primary"


def test_yaml_versions_do_not_leak_between_files():
    parsers = ParserSet()
    for data, expected in [
        (b"%YAML 1.1\n---\non\n", True),
        (b"%YAML 1.2\n---\non\n", "on"),
        (b"on\n", "on"),
        (b"%YAML 1.1\n---\nno\n", False),
    ]:
        assert parsers.parse_data_with_path(data, "input.yaml", "yaml") == expected


@pytest.mark.parametrize(
    "value,expected", [("yes", True), ("No", False), ("012", 10), ("1:20", 80)]
)
def test_explicit_yaml_11_scalars(value, expected):
    data = f"%YAML 1.1\n---\n{value}\n".encode()

    assert ParserSet().parse_data_with_path(data, "input.yaml", "yaml") == expected


@pytest.mark.parametrize("data", [b"\xff", codecs.BOM_UTF16_LE + b"\xff"])
def test_invalid_encodings_keep_yaml_parse_errors(data):
    with pytest.raises(FailedFileLoadError):
        ParserSet().parse_data_with_path(data, "input.yaml", "yaml")
