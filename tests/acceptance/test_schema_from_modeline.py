import json

import responses


def test_schema_from_modeline_validates_files_against_different_schemas(
    run_line_simple, tmp_path
):
    schemas = tmp_path / "schemas"
    configs = tmp_path / "configs"
    schemas.mkdir()
    configs.mkdir()

    (schemas / "name.json").write_text(
        json.dumps({"type": "object", "required": ["name"]})
    )
    (schemas / "count.json").write_text(
        json.dumps({"type": "object", "required": ["count"]})
    )

    name_config = configs / "name.yaml"
    count_config = configs / "count.yaml"
    name_config.write_text("""\
# yaml-language-server: $schema=../schemas/name.json
name: example
""")
    count_config.write_text("""\
# $schema: ../schemas/count.json
count: 1
""")

    run_line_simple(
        ["--schema-from-modeline", str(name_config), str(count_config)]
    )


def test_schema_from_modeline_reports_validation_errors(run_line, tmp_path):
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"type": "object", "required": ["name"]}))

    config = tmp_path / "config.yaml"
    config.write_text("""\
# yaml-language-server: $schema=schema.json
count: 1
""")

    result = run_line(["check-jsonschema", "--schema-from-modeline", str(config)])

    assert result.exit_code == 1
    assert f"{config}::$: 'name' is a required property" in result.stdout


def test_schema_from_modeline_skips_unannotated_files(run_line_simple, tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("this: is not validated")

    run_line_simple(["--schema-from-modeline", str(config)])


def test_schema_from_modeline_skips_unannotated_malformed_files(
    run_line_simple, tmp_path
):
    config = tmp_path / "config.yaml"
    config.write_text("a: {b")

    run_line_simple(["--schema-from-modeline", str(config)])


def test_schema_from_modeline_supports_remote_schemas(run_line_simple, tmp_path):
    schema_url = "https://example.com/schema.json"
    responses.add(
        "GET",
        schema_url,
        headers={"Last-Modified": "Sun, 01 Jan 2000 00:00:01 GMT"},
        json={"type": "object", "required": ["name"]},
        match_querystring=None,
    )

    config = tmp_path / "config.yaml"
    config.write_text(f"""\
# yaml-language-server: $schema={schema_url}
name: example
""")

    run_line_simple(["--schema-from-modeline", str(config)])


def test_schema_from_modeline_validates_each_yaml_document(run_line, tmp_path):
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"type": "object", "required": ["name"]}))

    config = tmp_path / "config.yaml"
    config.write_text("""\
# yaml-language-server: $schema=schema.json
---
name: ok
---
count: 1
""")

    result = run_line(["check-jsonschema", "--schema-from-modeline", str(config)])

    assert result.exit_code == 1
    assert f"{config}:5::$: 'name' is a required property" in result.stdout


def test_schema_from_modeline_preserves_top_level_yaml_lists(
    run_line_simple, tmp_path
):
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"type": "array", "items": {"type": "string"}}))

    config = tmp_path / "config.yaml"
    config.write_text("""\
# yaml-language-server: $schema=schema.json
- first
- second
""")

    run_line_simple(["--schema-from-modeline", str(config)])
