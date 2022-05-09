import json

CASE1_MAIN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "title": {"$ref": "./title_schema.yaml"},
    },
    "additionalProperties": False,
}
CASE1_TITLE_SCHEMA = {"type": "string"}
CASE1_PASSING_DOCUMENT = {"title": "doc one"}
CASE1_FAILING_DOCUMENT = {"title": 2}


def test_warning_on_yaml_reference_passes(run_line, tmp_path):
    main_schemafile = tmp_path / "main_schema.json"
    main_schemafile.write_text(json.dumps(CASE1_MAIN_SCHEMA))
    ref_schema = tmp_path / "title_schema.yaml"
    ref_schema.write_text(json.dumps(CASE1_TITLE_SCHEMA))

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(CASE1_PASSING_DOCUMENT))

    result = run_line(
        ["check-jsonschema", "--schemafile", str(main_schemafile), str(doc)]
    )
    assert result.exit_code == 0
    assert (
        "WARNING: You appear to be using a schema which references a YAML file"
        in result.stderr
    )


def test_warning_on_yaml_reference_fails(run_line, tmp_path):
    main_schemafile = tmp_path / "main_schema.json"
    main_schemafile.write_text(json.dumps(CASE1_MAIN_SCHEMA))
    ref_schema = tmp_path / "title_schema.yaml"
    ref_schema.write_text(json.dumps(CASE1_TITLE_SCHEMA))

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(CASE1_FAILING_DOCUMENT))

    result = run_line(
        ["check-jsonschema", "--schemafile", str(main_schemafile), str(doc)]
    )
    assert result.exit_code == 1
    assert (
        "WARNING: You appear to be using a schema which references a YAML file"
        in result.stderr
    )
