import json

import pytest

from check_jsonschema.parsers.json5 import ENABLED as JSON5_ENABLED

SIMPLE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "title": {"type": "string"},
    },
    "additionalProperties": False,
}
YAML_REF_MAIN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "title": {"$ref": "./title_schema.yaml"},
    },
    "additionalProperties": False,
}
JSON5_REF_MAIN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "title": {"$ref": "./title_schema.json5"},
    },
    "additionalProperties": False,
}
TITLE_SCHEMA = {"type": "string"}
PASSING_DOCUMENT = {"title": "doc one"}
FAILING_DOCUMENT = {"title": 2}


@pytest.mark.parametrize("passing_data", [True, False])
def test_warning_on_yaml_reference_passes(run_line, tmp_path, passing_data):
    main_schemafile = tmp_path / "main_schema.json"
    main_schemafile.write_text(json.dumps(YAML_REF_MAIN_SCHEMA))
    ref_schema = tmp_path / "title_schema.yaml"
    ref_schema.write_text(json.dumps(TITLE_SCHEMA))

    doc = tmp_path / "doc.json"
    if passing_data:
        doc.write_text(json.dumps(PASSING_DOCUMENT))
    else:
        doc.write_text(json.dumps(FAILING_DOCUMENT))

    result = run_line(
        ["check-jsonschema", "--schemafile", str(main_schemafile), str(doc)]
    )
    assert result.exit_code == (0 if passing_data else 1)
    assert (
        "WARNING: You appear to be using a schema which references a YAML file"
        in result.stderr
    )


@pytest.mark.parametrize("passing_data", [True, False])
def test_warning_on_json5_reference(run_line, tmp_path, passing_data):
    main_schemafile = tmp_path / "main_schema.json"
    main_schemafile.write_text(json.dumps(JSON5_REF_MAIN_SCHEMA))
    ref_schema = tmp_path / "title_schema.json5"
    ref_schema.write_text(json.dumps(TITLE_SCHEMA))

    doc = tmp_path / "doc.json"
    if passing_data:
        doc.write_text(json.dumps(PASSING_DOCUMENT))
    else:
        doc.write_text(json.dumps(FAILING_DOCUMENT))

    result = run_line(
        ["check-jsonschema", "--schemafile", str(main_schemafile), str(doc)]
    )
    assert result.exit_code == (0 if passing_data else 1)
    assert (
        "WARNING: You appear to be using a schema which references a JSON5 file"
        in result.stderr
    )


@pytest.mark.skipif(not JSON5_ENABLED, reason="test requires json5")
@pytest.mark.parametrize("passing_data", [True, False])
def test_can_load_json5_schema(run_line, tmp_path, passing_data):
    # dump JSON to the JSON5 file, this is fine
    main_schemafile = tmp_path / "main_schema.json5"
    main_schemafile.write_text(json.dumps(SIMPLE_SCHEMA))

    doc = tmp_path / "doc.json"
    if passing_data:
        doc.write_text(json.dumps(PASSING_DOCUMENT))
    else:
        doc.write_text(json.dumps(FAILING_DOCUMENT))

    result = run_line(
        ["check-jsonschema", "--schemafile", str(main_schemafile), str(doc)]
    )
    assert result.exit_code == (0 if passing_data else 1)
