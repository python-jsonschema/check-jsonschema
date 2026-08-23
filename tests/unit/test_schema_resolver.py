import pytest

from check_jsonschema.formats import FormatOptions
from check_jsonschema.regex_variants import RegexImplementation, RegexVariantName
from check_jsonschema.schema_loader import BuiltinSchemaLoader


@pytest.mark.parametrize(
    ("schema_name", "expected"),
    [
        ("vendor.dependabot", True),
        ("dependabot", True),
        ("custom.github-workflows-require-timeout", False),
        ("github-workflows-require-timeout", False),
    ],
)
def test_builtin_schema_loader_records_vendored_origin(schema_name, expected):
    loader = BuiltinSchemaLoader(schema_name)

    assert loader.is_vendored_schema is expected


@pytest.mark.parametrize(
    "base_uri",
    [
        "https://json.schemastore.org/base.json",
        "https://www.schemastore.org/base.json",
    ],
)
def test_vendored_schemastore_base_is_available_offline(base_uri, monkeypatch):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$ref": f"{base_uri}#/definitions/timezone",
    }

    def fail_on_download(*args, **kwargs):
        pytest.fail("the vendored reference should not require a download")

    monkeypatch.setattr(
        "check_jsonschema.schema_loader.resolver.CacheDownloader.bind",
        fail_on_download,
    )
    monkeypatch.setattr(
        "check_jsonschema.schema_loader.main.get_builtin_schema",
        lambda name: schema,
    )

    regex_impl = RegexImplementation(RegexVariantName.default)
    loader = BuiltinSchemaLoader("vendor.test")
    validator = loader.get_validator(
        "instance.json",
        {},
        FormatOptions(regex_impl=regex_impl, enabled=False),
        regex_impl,
        False,
    )

    assert validator.is_valid("Europe/Istanbul")
    assert not validator.is_valid("Mars/Olympus_Mons")
