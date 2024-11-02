import json

import pytest

# define a calendar event schema and then use a custom validator to validate that there
# are no events with "Occult" in their names
SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "definitions": {
        "calendar-event": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"},
            },
        }
    },
    "properties": {
        "events": {
            "type": "array",
            "items": {"$ref": "#/definitions/calendar-event"},
        },
    },
    "required": ["events"],
}
VALID_DOC = {
    "events": [
        {
            "title": "Weekly Production Meeting",
            "start": "2019-06-24T09:00:00-05:00",
            "end": "2019-06-24T10:00:00-05:00",
        },
        {
            "title": "Catch Up",
            "start": "2019-06-24T10:00:00-05:00",
            "end": "2019-06-24T10:30:00-05:00",
        },
    ]
}
INVALID_DOC = {
    "events": [
        {
            "title": "Weekly Production Meeting",
            "start": "2019-06-24T09:00:00-05:00",
            "end": "2019-06-24T10:00:00-05:00",
        },
        {
            "title": "Catch Up",
            "start": "2019-06-24T10:00:00-05:00",
            "end": "2019-06-24T10:30:00-05:00",
        },
        {
            "title": "Occult Study Session",
            "start": "2019-06-24T10:00:00-05:00",
            "end": "2019-06-24T12:00:00-05:00",
        },
    ]
}


@pytest.fixture(autouse=True)
def _foo_module(mock_module):
    mock_module(
        "foo.py",
        """\
import jsonschema


def check_occult_properties(validator, properties, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    for property, subschema in properties.items():
        if property in instance:
            if property == "title" and "Occult" in instance["title"]:
                yield jsonschema.exceptions.ValidationError(
                    "Error! Occult event detected! Run!",
                    validator=validator,
                    validator_value=None,
                    instance=instance,
                    schema=schema,
                )
            yield from validator.descend(
                instance[property],
                subschema,
                path=property,
                schema_path=property,
            )

MyValidator = jsonschema.validators.extend(
    jsonschema.validators.Draft7Validator,
    {"properties": check_occult_properties},
)
""",
    )


def test_custom_validator_class_can_detect_custom_conditions(run_line, tmp_path):
    doc = tmp_path / "invalid.json"
    doc.write_text(json.dumps(INVALID_DOC))

    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps(SCHEMA))

    result = run_line(
        [
            "check-jsonschema",
            "--schemafile",
            str(schema),
            str(doc),
        ]
    )
    assert result.exit_code == 0, result.stdout  # pass

    result = run_line(
        [
            "check-jsonschema",
            "--schemafile",
            str(schema),
            "--validator-class",
            "foo:MyValidator",
            str(doc),
        ],
    )
    assert result.exit_code == 1, result.stdout  # fail
    assert "Occult event detected" in result.stdout, result.stdout


def test_custom_validator_class_can_pass_when_valid(run_line, tmp_path):
    doc = tmp_path / "valid.json"
    doc.write_text(json.dumps(VALID_DOC))

    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps(SCHEMA))

    result = run_line(
        [
            "check-jsonschema",
            "--schemafile",
            str(schema),
            str(doc),
        ]
    )
    assert result.exit_code == 0, result.stdout  # pass

    result = run_line(
        [
            "check-jsonschema",
            "--schemafile",
            str(schema),
            "--validator-class",
            "foo:MyValidator",
            str(doc),
        ],
    )
    assert result.exit_code == 0  # pass


@pytest.mark.parametrize(
    "add_opts",
    (
        ["--builtin-schema", "vendor.github-workflows"],
        ["--check-metaschema"],
    ),
)
def test_custom_validator_class_is_incompatible_with_schema_opts(
    run_line, tmp_path, add_opts
):
    doc = tmp_path / "instance.json"
    doc.write_text("{}")
    result = run_line(
        [
            "check-jsonschema",
            "--validator-class",
            "foo:MyValidator",
            str(doc),
        ]
        + add_opts
    )
    assert result.exit_code == 2
    assert "--validator-class can only be used with --schemafile" in result.stderr
