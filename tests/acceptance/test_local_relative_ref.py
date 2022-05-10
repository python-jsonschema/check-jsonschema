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
CASE2_FAILING_DOCUMENT = {"test": {"foo": "bar"}}


def _prep_files(tmp_path, main_schema, other_schema_data, instance):
    main_schemafile = tmp_path / "main_schema.json"
    main_schemafile.write_text(json.dumps(main_schema))
    for k, v in other_schema_data.items():
        schemafile = tmp_path / k
        schemafile.write_text(json.dumps(v))
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(instance))
    return main_schemafile, doc


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
@pytest.mark.parametrize("with_file_scheme", [True, False])
def test_local_ref_schema(
    run_line_simple,
    tmp_path,
    main_schema,
    other_schema_data,
    instance,
    with_file_scheme,
):
    main_schemafile, doc = _prep_files(
        tmp_path, main_schema, other_schema_data, instance
    )
    if with_file_scheme:
        schemafile = main_schemafile.resolve().as_uri()
    else:
        schemafile = str(main_schemafile)
    run_line_simple(["--schemafile", schemafile, str(doc)])


@pytest.mark.parametrize(
    "main_schema, other_schema_data, instance, expect_err",
    [
        (
            CASE1_MAIN_SCHEMA,
            {"title_schema.json": CASE1_TITLE_SCHEMA},
            CASE1_FAILING_DOCUMENT,
            None,
        ),
        (
            CASE2_MAIN_SCHEMA,
            {"values.json": CASE2_VALUES_SCHEMA},
            CASE2_FAILING_DOCUMENT,
            "{'foo': 'bar'} is not of type 'string'",
        ),
    ],
)
@pytest.mark.parametrize("with_file_scheme", [True, False])
def test_local_ref_schema_failure_case(
    run_line,
    tmp_path,
    main_schema,
    other_schema_data,
    instance,
    expect_err,
    with_file_scheme,
):
    main_schemafile, doc = _prep_files(
        tmp_path, main_schema, other_schema_data, instance
    )
    if with_file_scheme:
        schemafile = main_schemafile.resolve().as_uri()
    else:
        schemafile = str(main_schemafile)
    res = run_line(["check-jsonschema", "--schemafile", schemafile, str(doc)])
    assert res.exit_code == 1
    if expect_err is not None:
        assert expect_err in res.stdout
