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
PASSING_DOCUMENT = """
// a comment
{"title": "doc one"}
"""
FAILING_DOCUMENT = """
// a comment
{"title": 2}
"""


@pytest.mark.skipif(not JSON5_ENABLED, reason="test requires json5")
@pytest.mark.parametrize("passing_data", [True, False])
def test_json5_filetype_forced_on_json_suffixed_instance(
    run_line, tmp_path, passing_data
):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(SIMPLE_SCHEMA))

    doc = tmp_path / "doc.json"
    if passing_data:
        doc.write_text(PASSING_DOCUMENT)
    else:
        doc.write_text(FAILING_DOCUMENT)

    result = run_line(
        [
            "check-jsonschema",
            "--force-filetype",
            "json5",
            "--schemafile",
            str(schemafile),
            str(doc),
        ]
    )
    assert result.exit_code == (0 if passing_data else 1)

    # but even in the passing case, a rerun without the force flag will fail
    if passing_data:
        result_without_filetype = run_line(
            [
                "check-jsonschema",
                "--schemafile",
                str(schemafile),
                str(doc),
            ]
        )
        assert result_without_filetype.exit_code == 1
