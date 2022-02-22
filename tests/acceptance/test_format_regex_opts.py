# test on a JavaScript regex which is not a valid python regex
# `--format-regex=disabled` should skip
# `--format-regex=default` should accept it
# `--format-regex=python` should reject it
#
# check these options against documents with invalid and valid python regexes to confirm
# that they are behaving as expected
import json

import pytest

FORMAT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {"pattern": {"type": "string", "format": "regex"}},
}

ALWAYS_PASSING_DOCUMENT = {
    "pattern": "ab*c",
}

ALWAYS_FAILING_DOCUMENT = {
    "pattern": "a(b*c",
}

JS_REGEX_DOCUMENT = {
    "pattern": "a(?<captured>)bc",
}

# taken from https://github.com/python-jsonschema/check-jsonschema/issues/25
RENOVATE_DOCUMENT = {
    "regexManagers": [
        {
            "fileMatch": ["^Dockerfile$"],
            "matchStrings": ["ENV YARN_VERSION=(?<currentValue>.*?)\n"],
            "depNameTemplate": "yarn",
            "datasourceTemplate": "npm",
        }
    ]
}


@pytest.mark.parametrize("regexopt", ["disabled", "default", "python"])
def test_regex_format_good(cli_runner, tmp_path, regexopt):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(ALWAYS_PASSING_DOCUMENT))

    cli_runner(["--format-regex", regexopt, "--schemafile", str(schemafile), str(doc)])


@pytest.mark.parametrize("regexopt", ["disabled", "default", "python"])
def test_regex_format_bad(cli_runner, tmp_path, regexopt):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(ALWAYS_FAILING_DOCUMENT))

    expect_ok = regexopt == "disabled"

    res = cli_runner(
        ["--format-regex", regexopt, "--schemafile", str(schemafile), str(doc)],
        expect_ok=expect_ok,
    )
    if not expect_ok:
        assert res.exit_code == 1


@pytest.mark.parametrize("regexopt", ["disabled", "default", "python"])
def test_regex_format_js_specific(cli_runner, tmp_path, regexopt):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(JS_REGEX_DOCUMENT))

    expect_ok = regexopt in ("disabled", "default")

    res = cli_runner(
        ["--format-regex", regexopt, "--schemafile", str(schemafile), str(doc)],
        expect_ok=expect_ok,
    )
    if not expect_ok:
        assert res.exit_code == 1


def test_regex_format_in_renovate_config(cli_runner, tmp_path):
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(RENOVATE_DOCUMENT))

    cli_runner(["--builtin-schema", "vendor.renovate", str(doc)])
