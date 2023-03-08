import json

FORMAT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "title": {
            "type": "string",
        },
        "date": {
            "type": "string",
            "format": "date",
        },
    },
}

PASSING_DOCUMENT = {
    "title": "doc one",
    "date": "2021-10-28",
}

FAILING_DOCUMENT = {
    "title": "doc one",
    "date": "foo",
}


def test_format_check_passing(run_line_simple, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc1 = tmp_path / "doc1.json"
    doc1.write_text(json.dumps(PASSING_DOCUMENT))

    run_line_simple(["--schemafile", str(schemafile), str(doc1)])


def test_format_failure_exit_error(run_line, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc1 = tmp_path / "doc1.json"
    doc1.write_text(json.dumps(FAILING_DOCUMENT))

    res = run_line(["check-jsonschema", "--schemafile", str(schemafile), str(doc1)])
    assert res.exit_code == 1


def test_format_failure_ignore(run_line_simple, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc1 = tmp_path / "doc1.json"
    doc1.write_text(json.dumps(FAILING_DOCUMENT))

    run_line_simple(
        [
            "--disable-formats",
            "*",
            "--schemafile",
            str(schemafile),
            str(doc1),
        ]
    )


def test_format_failure_ignore_multidoc(run_line_simple, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA))

    doc1 = tmp_path / "doc1.json"
    doc1.write_text(json.dumps(FAILING_DOCUMENT))

    doc2 = tmp_path / "doc2.json"
    doc2.write_text(json.dumps(PASSING_DOCUMENT))

    run_line_simple(
        [
            "--disable-formats",
            "*",
            "--schemafile",
            str(schemafile),
            str(doc1),
            str(doc2),
        ]
    )
