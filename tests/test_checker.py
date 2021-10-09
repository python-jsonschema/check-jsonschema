import pytest

from check_jsonschema.checker import SchemaChecker


def test_checker_non_json_schemafile(tmp_path, capsys):
    foo = tmp_path / "foo.json"
    bar = tmp_path / "bar.json"
    foo.write_text("{")
    bar.write_text("{}")

    checker = SchemaChecker(str(foo), [str(bar)])
    with pytest.raises(SystemExit):
        checker.get_validator()

    stdio = capsys.readouterr()
    assert "schemafile could not be parsed" in stdio.out


def test_checker_invalid_schemafile(tmp_path, capsys):
    foo = tmp_path / "foo.json"
    bar = tmp_path / "bar.json"
    foo.write_text('{"title": {"foo": "bar"}}')
    bar.write_text("{}")

    checker = SchemaChecker(str(foo), [str(bar)])
    with pytest.raises(SystemExit):
        checker.get_validator()

    stdio = capsys.readouterr()
    assert "schemafile was not valid" in stdio.out
