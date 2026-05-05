import pytest


def test_checker_unresolvable_schema_ref_has_concise_error(run_line, tmp_path):
    foo = tmp_path / "foo.json"
    bar = tmp_path / "bar.json"
    foo.write_text('{"properties": {"foo": {"$ref": "#/definitions/missing"}}}')
    bar.write_text('{"foo": "bar"}')

    res = run_line(["check-jsonschema", "--schemafile", str(foo), str(bar)])

    assert res.exit_code == 1
    assert "Schema validation errors were encountered." in res.stdout
    assert f"{bar}::$: A $ref in the schema could not be resolved" in res.stdout
    assert "PointerToNowhere: '/definitions/missing' does not exist" in res.stdout
    assert "'properties':" not in res.stdout


def test_checker_non_json_schemafile(run_line, tmp_path):
    foo = tmp_path / "foo.json"
    bar = tmp_path / "bar.json"
    foo.write_text("{")
    bar.write_text("{}")

    res = run_line(["check-jsonschema", "--schemafile", str(foo), str(bar)])
    assert res.exit_code == 1
    assert "schemafile could not be parsed" in res.stderr


def test_checker_invalid_schemafile(run_line, tmp_path):
    foo = tmp_path / "foo.json"
    bar = tmp_path / "bar.json"
    foo.write_text('{"title": {"foo": "bar"}}')
    bar.write_text("{}")

    res = run_line(["check-jsonschema", "--schemafile", str(foo), str(bar)])
    assert res.exit_code == 1
    assert "schemafile was not valid" in res.stderr


def test_checker_invalid_schemafile_scheme(run_line, tmp_path):
    foo = tmp_path / "foo.json"
    bar = tmp_path / "bar.json"
    foo.write_text('{"title": "foo"}')
    bar.write_text("{}")

    res = run_line(["check-jsonschema", "--schemafile", f"ftp://{foo}", str(bar)])
    assert res.exit_code == 1
    assert "only supports http, https" in res.stderr


@pytest.mark.parametrize(
    "add_args",
    [
        pytest.param([], id="noargs"),
        # ensure that this works even when regex checking is disabled
        pytest.param(["--disable-formats", "*"], id="all-formats-disabled"),
        pytest.param(["--disable-formats", "regex"], id="regex-format-disabled"),
    ],
)
def test_checker_invalid_schemafile_due_to_bad_regex(run_line, tmp_path, add_args):
    foo = tmp_path / "foo.json"
    bar = tmp_path / "bar.json"
    # too many backslash escapes -- not a valid Unicode-mode regex
    foo.write_text(r'{"properties": {"foo": {"pattern": "\\\\p{N}"}}}')
    bar.write_text("{}")

    res = run_line(["check-jsonschema", "--schemafile", str(foo), str(bar), *add_args])
    assert res.exit_code == 1
    assert "schemafile was not valid" in res.stderr
