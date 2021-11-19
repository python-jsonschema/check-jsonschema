import json

import pytest

CASE1_MAIN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "title": {"$ref": "./title_schema.json"},
    },
    "additionalProperties": False,
}
CASE1_TITLE_SCHEMA = {
    "type": "string",
}
CASE1_PASSING_DOCUMENT = {"title": "doc one"}
CASE1_FAILING_DOCUMENT = {"title": 2}


CASE2_MAIN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "type": "object",
    "required": ["test"],
    "properties": {"test": {"$ref": "./values.json#/$defs/test"}},
}
CASE2_VALUES_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "$defs": {"test": {"type": "string"}},
}
CASE2_PASSING_DOCUMENT = {"test": "some data"}


@pytest.mark.parametrize(
    "main_schema, other_schema_data, instance",
    [
        (
            CASE1_MAIN_SCHEMA,
            {"title_schema.json": CASE1_TITLE_SCHEMA},
            CASE1_PASSING_DOCUMENT,
        ),
        (
            CASE2_MAIN_SCHEMA,
            {"values.json": CASE2_VALUES_SCHEMA},
            CASE2_PASSING_DOCUMENT,
        ),
    ],
)
def test_local_ref_schema(
    cli_runner, tmp_path, main_schema, other_schema_data, instance
):
    main_schemafile = tmp_path / "main_schema.json"
    main_schemafile.write_text(json.dumps(main_schema))
    for k, v in other_schema_data.items():
        schemafile = tmp_path / k
        schemafile.write_text(json.dumps(v))
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(instance))

    cli_runner(["--schemafile", str(main_schemafile), str(doc)])


def test_local_ref_schema_failure_case(cli_runner, tmp_path):
    main_schemafile = tmp_path / "main_schema.json"
    main_schemafile.write_text(json.dumps(CASE1_MAIN_SCHEMA))
    title_schemafile = tmp_path / "title_schema.json"
    title_schemafile.write_text(json.dumps(CASE1_TITLE_SCHEMA))

    doc2 = tmp_path / "doc2.json"
    doc2.write_text(json.dumps(CASE1_FAILING_DOCUMENT))

    res = cli_runner(["--schemafile", str(main_schemafile), str(doc2)], expect_ok=False)
    assert res.exit_code == 1
