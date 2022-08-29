import json

import pytest

TITLE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {"title": {"type": "string"}},
    "required": ["title"],
}


def test_non_json_instance(run_line, tmp_path):
    schema = tmp_path / "schema.json"
    instance = tmp_path / "instance.json"
    schema.write_text("{}")
    instance.write_text("{")

    res = run_line(["check-jsonschema", "--schemafile", str(schema), str(instance)])
    assert res.exit_code == 1
    assert f"Failed to parse {str(instance)}" in res.stdout


@pytest.mark.parametrize("outformat", ["TEXT", "JSON"])
def test_non_json_instance_mixed_with_valid_data(run_line, tmp_path, outformat):
    schema = tmp_path / "schema.json"
    malformed_instance = tmp_path / "malformed_instance.json"
    good_instance = tmp_path / "good_instance.json"
    schema.write_text(json.dumps(TITLE_SCHEMA))
    malformed_instance.write_text("{")
    good_instance.write_text('{"title": "ohai"}')

    res = run_line(
        [
            "check-jsonschema",
            "-o",
            outformat,
            "--schemafile",
            str(schema),
            str(malformed_instance),
            str(good_instance),
        ]
    )
    assert res.exit_code == 1
    if outformat == "TEXT":
        assert f"Failed to parse {str(malformed_instance)}" in res.stdout
    else:
        report = json.loads(res.stdout)
        assert report["status"] == "fail"
        assert "errors" in report
        assert report["errors"] == []
        assert "parse_errors" in report
        assert len(report["parse_errors"]) == 1
        error_item = report["parse_errors"][0]
        assert error_item["filename"] == str(malformed_instance)
        assert f"Failed to parse {str(malformed_instance)}" in error_item["message"]


@pytest.mark.parametrize("outformat", ["TEXT", "JSON"])
def test_non_json_instance_mixed_with_valid_and_invalid_data(
    run_line, tmp_path, outformat
):
    schema = tmp_path / "schema.json"
    malformed_instance = tmp_path / "malformed_instance.json"
    good_instance = tmp_path / "good_instance.json"
    bad_instance = tmp_path / "bad_instance.json"
    schema.write_text(json.dumps(TITLE_SCHEMA))
    malformed_instance.write_text("{")
    good_instance.write_text('{"title": "ohai"}')
    bad_instance.write_text('{"title": false}')

    res = run_line(
        [
            "check-jsonschema",
            "-o",
            outformat,
            "--schemafile",
            str(schema),
            str(good_instance),
            str(malformed_instance),
            str(bad_instance),
        ]
    )
    assert res.exit_code == 1
    if outformat == "TEXT":
        assert f"Failed to parse {str(malformed_instance)}" in res.stdout
        assert (
            f"{str(bad_instance)}::$.title: False is not of type 'string'" in res.stdout
        )
    else:
        report = json.loads(res.stdout)
        assert report["status"] == "fail"

        assert "errors" in report
        assert len(report["errors"]) == 1

        assert "parse_errors" in report
        assert len(report["parse_errors"]) == 1
        error_item = report["parse_errors"][0]
        assert error_item["filename"] == str(malformed_instance)
        assert f"Failed to parse {str(malformed_instance)}" in error_item["message"]
