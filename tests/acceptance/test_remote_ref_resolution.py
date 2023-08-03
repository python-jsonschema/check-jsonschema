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


@pytest.fixture(autouse=True)
def _mock_schema_cache_dir(monkeypatch, tmp_path):
    def _fake_compute_default_cache_dir(self):
        return str(tmp_path)

    monkeypatch.setattr(
        cachedownloader.CacheDownloader,
        "_compute_default_cache_dir",
        _fake_compute_default_cache_dir,
    )


@pytest.mark.parametrize("check_passes", (True, False))
@pytest.mark.parametrize("casename", ("case1", "case2"))
def test_remote_ref_resolution_simple_case(run_line, check_passes, casename, tmp_path):
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


# this test ensures that `$id` is preferred for the base URI over
# the retrieval URI
@pytest.mark.parametrize("check_passes", (True, False))
def test_ref_resolution_prefers_id_over_retrieval_uri(run_line, tmp_path, check_passes):
    main_schema = {
        "$id": "https://example.org/schemas/main.json",
        "$schema": "http://json-schema.org/draft-07/schema",
        "properties": {
            "title": {"$ref": "./title_schema.json"},
        },
        "additionalProperties": False,
    }
    title_schema = {"type": "string"}

    retrieval_uri = "https://example.org/alternate-path-retrieval-only/schemas/main"
    responses.add("GET", retrieval_uri, json=main_schema)
    responses.add(
        "GET", "https://example.org/schemas/title_schema.json", json=title_schema
    )

    instance_path = tmp_path / "instance.json"
    instance_path.write_text(json.dumps({"title": "doc one" if check_passes else 2}))

    result = run_line(
        ["check-jsonschema", "--schemafile", retrieval_uri, str(instance_path)]
    )
    output = f"\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    if check_passes:
        assert result.exit_code == 0, output
    else:
        assert result.exit_code == 1, output


@pytest.mark.parametrize("check_passes", (True, False))
def test_ref_resolution_does_not_callout_for_absolute_ref_to_retrieval_uri(
    run_line, tmp_path, check_passes
):
    retrieval_uri = "https://example.net/schemas/main"

    main_schema = {
        "$id": "https://example.net/schemas/some-uri-which-will-never-be-used/main.json",
        "$schema": "http://json-schema.org/draft-07/schema",
        "$defs": {"title": {"type": "string"}},
        "properties": {
            "title": {"$ref": f"{retrieval_uri}#/$defs/title"},
        },
        "additionalProperties": False,
    }

    # exactly one GET to the retrieval URI will work
    responses.add("GET", retrieval_uri, json=main_schema)
    responses.add("GET", retrieval_uri, json={"error": "permafrost melted"}, status=500)

    instance_path = tmp_path / "instance.json"
    instance_path.write_text(json.dumps({"title": "doc one" if check_passes else 2}))

    result = run_line(
        ["check-jsonschema", "--schemafile", retrieval_uri, str(instance_path)]
    )
    output = f"\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    if check_passes:
        assert result.exit_code == 0, output
    else:
        assert result.exit_code == 1, output
