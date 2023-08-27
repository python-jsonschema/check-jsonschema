import json
import textwrap

import pytest
from jsonschema import Draft7Validator

from check_jsonschema.reporter import JsonReporter, TextReporter
from check_jsonschema.result import CheckResult


def _make_success_result():
    res = CheckResult()
    res.successes.append("foo.json")
    return res


@pytest.mark.parametrize("verbosity", (0, 1, 2))
@pytest.mark.parametrize("use_report_result_path", (False, True))
def test_text_format_success(capsys, verbosity, use_report_result_path):
    reporter = TextReporter(verbosity=verbosity)
    if use_report_result_path:
        reporter.report_result(_make_success_result())
    else:
        reporter.report_success(_make_success_result())
    captured = capsys.readouterr()
    assert captured.err == ""
    if verbosity == 0:
        assert captured.out == ""
    elif verbosity == 1:
        assert captured.out == "ok -- validation done\n"
    else:
        assert captured.out == textwrap.dedent(
            """\
            ok -- validation done
            The following files were checked:
              foo.json
            """
        )


@pytest.mark.parametrize("verbosity", (0, 1, 2))
@pytest.mark.parametrize("use_report_result_path", (False, True))
def test_json_format_success(capsys, verbosity, use_report_result_path):
    reporter = JsonReporter(verbosity=verbosity, pretty=False)
    if use_report_result_path:
        reporter.report_result(_make_success_result())
    else:
        reporter.report_success(_make_success_result())
    captured = capsys.readouterr()
    assert captured.err == ""
    if verbosity == 0:
        assert captured.out == '{"status":"ok"}\n'
    elif verbosity == 1:
        assert captured.out == '{"status":"ok","errors":[]}\n'
    else:
        assert (
            captured.out == '{"status":"ok","errors":[],"checked_paths":["foo.json"]}\n'
        )


def test_text_format_validation_error_message_simple():
    validator = Draft7Validator(
        {
            "properties": {
                "foo": {
                    "anyOf": [
                        {"type": "string"},
                        {"properties": {"bar": {"type": "array"}}},
                    ],
                },
            },
        },
    )
    err = next(validator.iter_errors({"foo": {"bar": 1}}))

    text_reporter = TextReporter(verbosity=1)
    s1 = text_reporter._format_validation_error_message(err, filename="foo.json")
    assert s1 == (
        "\x1b[33mfoo.json::$.foo\x1b[0m: {'bar': 1} "
        "is not valid under any of the given schemas"
    )

    s2 = text_reporter._format_validation_error_message(err)
    assert s2 == (
        "\x1b[33m$.foo\x1b[0m: {'bar': 1} "
        "is not valid under any of the given schemas"
    )


@pytest.mark.parametrize("verbosity", (0, 1, 2))
def test_text_print_validation_error_nested(capsys, verbosity):
    validator = Draft7Validator(
        {
            "anyOf": [
                {
                    "properties": {
                        "foo": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "integer"},
                            ],
                        },
                    },
                },
                {
                    "properties": {
                        "bar": {
                            "oneOf": [
                                {"type": "string"},
                                {
                                    "type": "object",
                                    "properties": {"baz": {"type": "integer"}},
                                },
                            ]
                        }
                    }
                },
            ]
        },
    )
    err = next(validator.iter_errors({"foo": {}, "bar": {"baz": "buzz"}}))

    result = CheckResult()
    result.record_validation_error("foo.json", err)

    text_reporter = TextReporter(verbosity=verbosity)
    text_reporter.report_result(result)
    captured = capsys.readouterr()
    # nothing to stderr
    assert captured.err == ""

    # if verbosity<1 stop here
    if verbosity < 1:
        assert captured.out == ""
        return

    # only assert part of the message
    # dict member order isn't guaranteed and isn't relevant here
    assert "is not valid under any of the given schemas" in captured.out
    assert "Underlying errors" in captured.out

    # we don't know which error was the best match (algo for best match could change)
    # so just assert the presence of the underlying error messages at higher verbosity
    if verbosity > 1:
        assert "$.foo: {} is not of type 'string'" in captured.out
        assert "$.bar: {'baz': 'buzz'} is not of type 'string'" in captured.out
        assert "$.bar.baz: 'buzz' is not of type 'integer'" in captured.out
    else:
        assert (
            "4 other errors were produced. Use '--verbose' to see all errors."
            in captured.out
        )


@pytest.mark.parametrize("pretty_json", (True, False))
@pytest.mark.parametrize("verbosity", (0, 1, 2))
def test_json_format_validation_error_nested(capsys, pretty_json, verbosity):
    validator = Draft7Validator(
        {
            "anyOf": [
                {
                    "properties": {
                        "foo": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "integer"},
                            ],
                        },
                    },
                },
                {
                    "properties": {
                        "bar": {
                            "oneOf": [
                                {"type": "string"},
                                {
                                    "type": "object",
                                    "properties": {"baz": {"type": "integer"}},
                                },
                            ]
                        }
                    }
                },
            ]
        },
    )
    err = next(validator.iter_errors({"foo": {}, "bar": {"baz": "buzz"}}))

    result = CheckResult()
    result.record_validation_error("foo.json", err)

    json_reporter = JsonReporter(pretty=pretty_json, verbosity=verbosity)
    json_reporter.report_result(result)
    captured = capsys.readouterr()
    # nothing to stderr
    assert captured.err == ""

    # json data to stdout, parse it
    data = json.loads(captured.out)
    assert data["status"] == "fail"

    # stop here unless verbosity>=1
    if verbosity < 1:
        assert data == {"status": "fail"}
        return

    assert len(data["errors"]) == 1
    assert "is not valid under any of the given schemas" in data["errors"][0]["message"]
    assert data["errors"][0]["has_sub_errors"]
    assert data["errors"][0]["num_sub_errors"] == 5

    # stop here unless 'verbosity>=2'
    if verbosity < 2:
        assert "sub_errors" not in data["errors"][0]
        return
    else:
        assert "sub_errors" in data["errors"][0]

    sub_errors = data["errors"][0]["sub_errors"]

    foo_errors, bar_errors, bar_baz_errors = [], [], []
    for error_item in sub_errors:
        if error_item["path"] == "$.foo":
            foo_errors.append(error_item)
        elif error_item["path"] == "$.bar":
            bar_errors.append(error_item)
        elif error_item["path"] == "$.bar.baz":
            bar_baz_errors.append(error_item)
    assert len(foo_errors) == 3
    assert len(bar_baz_errors) == 1
    assert len(bar_errors) == 2

    assert "'buzz' is not of type 'integer'" == bar_baz_errors[0]["message"]
    assert {item["message"] for item in foo_errors} == {
        "{} is not of type 'string'",
        "{} is not of type 'integer'",
        "{} is not valid under any of the given schemas",
    }

    assert "{'baz': 'buzz'} is not of type 'string'" in [
        item["message"] for item in bar_errors
    ]
