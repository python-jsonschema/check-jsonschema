import json

import pytest
import responses

from check_jsonschema import cachedownloader

CASES = {
    "case1": {
        "main_schema": {
            "$schema": "http://json-schema.org/draft-07/schema",
            "properties": {
                "title": {"$ref": "./title_schema.json"},
            },
            "additionalProperties": False,
        },
        "other_schemas": {"title_schema": {"type": "string"}},
        "passing_document": {"title": "doc one"},
        "failing_document": {"title": 2},
    },
    "case2": {
        "main_schema": {
            "$schema": "http://json-schema.org/draft-07/schema",
            "type": "object",
            "required": ["test"],
            "properties": {"test": {"$ref": "./values.json#/$defs/test"}},
        },
        "other_schemas": {
            "values": {
                "$schema": "http://json-schema.org/draft-07/schema",
                "$defs": {"test": {"type": "string"}},
            }
        },
        "passing_document": {"test": "some data"},
        "failing_document": {"test": {"foo": "bar"}},
    },
}


@pytest.mark.parametrize("check_passes", (True, False))
@pytest.mark.parametrize("casename", ("case1", "case2"))
def test_remote_ref_resolution_simple_case(
    run_line, check_passes, casename, tmp_path, monkeypatch
):
    def _fake_compute_default_cache_dir(self):
        return str(tmp_path)

    monkeypatch.setattr(
        cachedownloader.CacheDownloader,
        "_compute_default_cache_dir",
        _fake_compute_default_cache_dir,
    )

    main_schema_loc = "https://example.com/main.json"
    responses.add("GET", main_schema_loc, json=CASES[casename]["main_schema"])
    for name, subschema in CASES[casename]["other_schemas"].items():
        other_schema_loc = f"https://example.com/{name}.json"
        responses.add("GET", other_schema_loc, json=subschema)

    instance_path = tmp_path / "instance.json"
    instance_path.write_text(
        json.dumps(
            CASES[casename]["passing_document"]
            if check_passes
            else CASES[casename]["failing_document"]
        )
    )

    result = run_line(
        ["check-jsonschema", "--schemafile", main_schema_loc, str(instance_path)]
    )
    output = f"\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    if check_passes:
        assert result.exit_code == 0, output
    else:
        assert result.exit_code == 1, output
