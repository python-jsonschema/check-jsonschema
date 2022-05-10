import json

import pytest
from jsonschema import Draft7Validator

from check_jsonschema.reporter import JsonReporter, TextReporter


def test_text_format_success(capsys):
    reporter = TextReporter(color=False)
    reporter.report_success()
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == "ok -- validation done\n"


def test_json_format_success(capsys):
    reporter = JsonReporter()
    reporter.report_success()
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == '{"status":"ok","errors":[]}\n'


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

    text_reporter = TextReporter(color=False)
    s1 = text_reporter._format_validation_error_message(err, filename="foo.json")
    assert (
        s1 == "foo.json::$.foo: {'bar': 1} is not valid under any of the given schemas"
    )

    s2 = text_reporter._format_validation_error_message(err)
    assert s2 == "$.foo: {'bar': 1} is not valid under any of the given schemas"


def test_text_print_validation_error_nested(capsys):
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

    text_reporter = TextReporter(color=False, show_all_errors=True)
    text_reporter._show_validation_error("foo.json", err)
    captured = capsys.readouterr()
    # nothing to stderr
    assert captured.err == ""

    # only assert part of the message
    # dict member order isn't guaranteed and isn't relevant here
    assert "is not valid under any of the given schemas" in captured.out
    assert "Underlying errors" in captured.out
    assert "$.bar: {'baz': 'buzz'} is not of type 'string'" in captured.out
    assert "$.bar.baz: 'buzz' is not of type 'integer'" in captured.out


@pytest.mark.parametrize("pretty_json", (True, False))
def test_json_format_validation_error_nested(capsys, pretty_json):
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

    json_reporter = JsonReporter(pretty=pretty_json, show_all_errors=True)
    json_reporter.report_validation_errors({"foo.json": [err]})
    captured = capsys.readouterr()
    # nothing to stderr
    assert captured.err == ""

    # json data to stdout, parse it
    data = json.loads(captured.out)
    assert data["status"] == "fail"
    assert len(data["errors"]) == 1
    assert "is not valid under any of the given schemas" in data["errors"][0]["message"]
    assert data["errors"][0]["has_sub_errors"]
    foo_errors, bar_errors, bar_baz_errors = [], [], []
    for error_item in data["errors"][0]["sub_errors"]:
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
