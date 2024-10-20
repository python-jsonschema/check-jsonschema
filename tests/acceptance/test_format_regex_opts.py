# test on a JavaScript regex which is not a valid python regex
# `--regex-variant=default` should accept it
# `--regex-variant=python` should reject it
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


@pytest.fixture(
    params=[
        ("--disable-formats", "regex"),
        ("--format-regex", "default"),
        ("--format-regex", "python"),
        ("--regex-variant", "python"),
        ("--regex-variant", "default"),
        ("--regex-variant", "default", "--format-regex", "python"),
        ("--regex-variant", "python", "--format-regex", "default"),
    ]
)
def regexopts(request):
    return request.param


def test_regex_format_good(run_line_simple, tmp_path, regexopts):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(ALWAYS_PASSING_DOCUMENT))

    run_line_simple([*regexopts, "--schemafile", str(schemafile), str(doc)])


def test_regex_format_accepts_non_str_inputs(run_line_simple, tmp_path, regexopts):
    # potentially confusing, but a format checker is allowed to check non-str instances
    # validate the format checker behavior on such a case
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(
        json.dumps(
            {
                "$schema": "http://json-schema.org/draft-07/schema",
                "properties": {"pattern": {"type": "integer", "format": "regex"}},
            }
        )
    )
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps({"pattern": 0}))
    run_line_simple([*regexopts, "--schemafile", str(schemafile), str(doc)])


def test_regex_format_bad(run_line, tmp_path, regexopts):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(ALWAYS_FAILING_DOCUMENT))

    expect_ok = regexopts == ("--disable-formats", "regex")

    res = run_line(
        [
            "check-jsonschema",
            *regexopts,
            "--schemafile",
            str(schemafile),
            str(doc),
        ],
    )
    if expect_ok:
        assert res.exit_code == 0
    else:
        assert res.exit_code == 1
        assert "is not a 'regex'" in res.stdout


def test_regex_format_js_specific(run_line, tmp_path, regexopts):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(JS_REGEX_DOCUMENT))

    expect_ok = regexopts[:2] not in (
        ("--format-regex", "python"),
        ("--regex-variant", "python"),
    )

    res = run_line(
        [
            "check-jsonschema",
            *regexopts,
            "--schemafile",
            str(schemafile),
            str(doc),
        ],
    )
    if expect_ok:
        assert res.exit_code == 0
    else:
        assert res.exit_code == 1
        assert "is not a 'regex'" in res.stdout


def test_regex_format_in_renovate_config(run_line_simple, tmp_path):
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(RENOVATE_DOCUMENT))

    run_line_simple(["--builtin-schema", "vendor.renovate", str(doc)])
