import json

MAIN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "title": {"$ref": "./title_schema.json"},
    },
    "additionalProperties": False,
}

TITLE_SCHEMA = {
    "type": "string",
}

PASSING_DOCUMENT = {"title": "doc one"}
FAILING_DOCUMENT = {"title": 2}


def test_local_ref_schema(cli_runner, tmp_path):
    main_schemafile = tmp_path / "main_schema.json"
    main_schemafile.write_text(json.dumps(MAIN_SCHEMA))
    title_schemafile = tmp_path / "title_schema.json"
    title_schemafile.write_text(json.dumps(TITLE_SCHEMA))

    doc1 = tmp_path / "doc1.json"
    doc1.write_text(json.dumps(PASSING_DOCUMENT))

    cli_runner(["--schemafile", str(main_schemafile), str(doc1)])


def test_local_ref_schema_failure_case(cli_runner, tmp_path):
    main_schemafile = tmp_path / "main_schema.json"
    main_schemafile.write_text(json.dumps(MAIN_SCHEMA))
    title_schemafile = tmp_path / "title_schema.json"
    title_schemafile.write_text(json.dumps(TITLE_SCHEMA))

    doc2 = tmp_path / "doc2.json"
    doc2.write_text(json.dumps(FAILING_DOCUMENT))

    res = cli_runner(["--schemafile", str(main_schemafile), str(doc2)], expect_ok=False)
    assert res.exit_code == 1
