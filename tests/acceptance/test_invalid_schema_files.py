def test_checker_non_json_schemafile(cli_runner, tmp_path):
    foo = tmp_path / "foo.json"
    bar = tmp_path / "bar.json"
    foo.write_text("{")
    bar.write_text("{}")

    res = cli_runner(["--schemafile", str(foo), str(bar)], expect_ok=False)
    assert res.exit_code == 1
    assert "schemafile could not be parsed" in res.stderr


def test_checker_invalid_schemafile(cli_runner, tmp_path):
    foo = tmp_path / "foo.json"
    bar = tmp_path / "bar.json"
    foo.write_text('{"title": {"foo": "bar"}}')
    bar.write_text("{}")

    res = cli_runner(["--schemafile", str(foo), str(bar)], expect_ok=False)
    assert res.exit_code == 1
    assert "schemafile was not valid" in res.stderr
