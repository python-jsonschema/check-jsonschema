import json

SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "title": {
            "type": "string",
            "default": "Untitled",
        },
    },
    "required": ["title"],
}

VALID_DOC = {
    "title": "doc one",
}

INVALID_DOC = {"title": {"foo": "bar"}}

MISSING_FIELD_DOC = {}


def test_run_with_fill_defaults_does_not_make_valid_doc_invalid(
    run_line_simple, tmp_path
):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(SCHEMA))

    doc = tmp_path / "instance.json"
    doc.write_text(json.dumps(VALID_DOC))

    run_line_simple(["--fill-defaults", "--schemafile", str(schemafile), str(doc)])


def test_run_with_fill_defaults_does_not_make_invalid_doc_valid(run_line, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(SCHEMA))

    doc = tmp_path / "instance.json"
    doc.write_text(json.dumps(INVALID_DOC))

    res = run_line(
        [
            "check-jsonschema",
            "--fill-defaults",
            "--schemafile",
            str(schemafile),
            str(doc),
        ]
    )
    assert res.exit_code == 1


def test_run_with_fill_defaults_adds_required_field(run_line, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(SCHEMA))

    doc = tmp_path / "instance.json"
    doc.write_text(json.dumps(MISSING_FIELD_DOC))

    # step 1: run without '--fill-defaults' and confirm failure
    result_without_fill_defaults = run_line(
        [
            "check-jsonschema",
            "--schemafile",
            str(schemafile),
            str(doc),
        ]
    )
    assert result_without_fill_defaults.exit_code == 1

    # step 2: run with '--fill-defaults' and confirm success
    result_with_fill_defaults = run_line(
        [
            "check-jsonschema",
            "--fill-defaults",
            "--schemafile",
            str(schemafile),
            str(doc),
        ]
    )
    assert result_with_fill_defaults.exit_code == 0
