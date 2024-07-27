import json

import pytest
import responses

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


@pytest.mark.parametrize("casename", ("case1", "case2"))
@pytest.mark.parametrize("disable_cache", (True, False))
def test_remote_ref_resolution_cache_control(
    run_line, tmp_path, get_ref_cache_loc, casename, disable_cache
):
    main_schema_loc = "https://example.com/main.json"
    responses.add("GET", main_schema_loc, json=CASES[casename]["main_schema"])

    ref_locs = []
    for name, subschema in CASES[casename]["other_schemas"].items():
        other_schema_loc = f"https://example.com/{name}.json"
        responses.add("GET", other_schema_loc, json=subschema)
        ref_locs.append(other_schema_loc)

    instance_path = tmp_path / "instance.json"
    instance_path.write_text(json.dumps(CASES[casename]["passing_document"]))

    # run the command
    result = run_line(
        ["check-jsonschema", "--schemafile", main_schema_loc, str(instance_path)]
        + (["--no-cache"] if disable_cache else [])
    )
    output = f"\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    assert result.exit_code == 0, output

    cache_locs = []
    for ref_loc in ref_locs:
        cache_locs.append(get_ref_cache_loc(ref_loc))
    assert cache_locs  # sanity check
    if disable_cache:
        for loc in cache_locs:
            assert not loc.exists()
    else:
        for loc in cache_locs:
            assert loc.exists()


@pytest.mark.parametrize("casename", ("case1", "case2"))
@pytest.mark.parametrize("check_passes", (True, False))
def test_remote_ref_resolution_loads_from_cache(
    run_line, tmp_path, get_ref_cache_loc, inject_cached_ref, casename, check_passes
):
    main_schema_loc = "https://example.com/main.json"
    responses.add("GET", main_schema_loc, json=CASES[casename]["main_schema"])

    ref_locs = []
    cache_locs = []
    for name, subschema in CASES[casename]["other_schemas"].items():
        other_schema_loc = f"https://example.com/{name}.json"
        # intentionally populate the HTTP location with "bad data"
        responses.add("GET", other_schema_loc, json="{}")
        ref_locs.append(other_schema_loc)

        # but populate the cache with "good data"
        inject_cached_ref(other_schema_loc, json.dumps(subschema))
        cache_locs.append(get_ref_cache_loc(other_schema_loc))

    instance_path = tmp_path / "instance.json"
    instance_path.write_text(
        json.dumps(
            CASES[casename]["passing_document"]
            if check_passes
            else CASES[casename]["failing_document"]
        )
    )

    # run the command
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


# this test ensures that `$id` is overwritten when `--base-uri` is used
@pytest.mark.parametrize("check_passes", (True, False))
def test_ref_resolution_with_custom_base_uri(run_line, tmp_path, check_passes):
    retrieval_uri = "https://example.org/retrieval-and-in-schema-only/schemas/main"
    explicit_base_uri = "https://example.org/schemas/main"
    main_schema = {
        "$id": retrieval_uri,
        "$schema": "http://json-schema.org/draft-07/schema",
        "properties": {
            "title": {"$ref": "./title_schema.json"},
        },
        "additionalProperties": False,
    }
    title_schema = {"type": "string"}

    responses.add("GET", retrieval_uri, json=main_schema)
    responses.add(
        "GET", "https://example.org/schemas/title_schema.json", json=title_schema
    )

    instance_path = tmp_path / "instance.json"
    instance_path.write_text(json.dumps({"title": "doc one" if check_passes else 2}))

    result = run_line(
        [
            "check-jsonschema",
            "--schemafile",
            retrieval_uri,
            "--base-uri",
            explicit_base_uri,
            str(instance_path),
        ]
    )
    output = f"\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    if check_passes:
        assert result.exit_code == 0, output
    else:
        assert result.exit_code == 1, output


@pytest.mark.parametrize("num_instances", (1, 2, 10))
@pytest.mark.parametrize("check_passes", (True, False))
def test_remote_ref_resolution_callout_count_is_scale_free_in_instancefiles(
    run_line, tmp_path, num_instances, check_passes
):
    """
    Test that for any N > 1, validation of a schema with a ref against N instance files
    has exactly the same number of callouts as validation when N=1

    This proves that the validator and caching are working correctly, and we aren't
    repeating callouts to rebuild state.
    """
    schema_uri = "https://example.org/schemas/main.json"
    ref_uri = "https://example.org/schemas/title_schema.json"

    main_schema = {
        "$id": schema_uri,
        "$schema": "http://json-schema.org/draft-07/schema",
        "properties": {
            "title": {"$ref": "./title_schema.json"},
        },
        "additionalProperties": False,
    }
    title_schema = {"type": "string"}
    responses.add("GET", schema_uri, json=main_schema)
    responses.add("GET", ref_uri, json=title_schema)

    # write N documents
    instance_doc = {"title": "doc one" if check_passes else 2}
    instance_paths = []
    for i in range(num_instances):
        instance_path = tmp_path / f"instance{i}.json"
        instance_path.write_text(json.dumps(instance_doc))
        instance_paths.append(str(instance_path))

    result = run_line(
        [
            "check-jsonschema",
            "--schemafile",
            schema_uri,
        ]
        + instance_paths
    )
    output = f"\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    if check_passes:
        assert result.exit_code == 0, output
    else:
        assert result.exit_code == 1, output

    # this is the moment of the "real" test run here:
    # no matter how many instances there were, there should only have been two calls
    # (one for the schema and one for the $ref)
    assert len(responses.calls) == 2
    assert len([c for c in responses.calls if c.request.url == schema_uri]) == 1
    assert len([c for c in responses.calls if c.request.url == ref_uri]) == 1
