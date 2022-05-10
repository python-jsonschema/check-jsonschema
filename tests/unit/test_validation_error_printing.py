import re

import pytest
from jsonschema import Draft7Validator

from check_jsonschema.reporter import TextReporter

# ANSI escape regex -- there are variations on this, but an excellent version
# was provided on SO by Martijn Pieters:
#    https://stackoverflow.com/a/14693789/2669818
# 7-bit C1 ANSI sequences
ANSI_ESCAPE = re.compile(
    r"""
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
""",
    re.VERBOSE,
)


@pytest.fixture
def text_reporter():
    return TextReporter()


def strip_ansi(text):
    return ANSI_ESCAPE.sub("", text)


def test_format_validation_error_message_simple(text_reporter):
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

    s1 = strip_ansi(
        text_reporter._format_validation_error_message(err, filename="foo.json")
    )
    assert (
        s1 == "foo.json::$.foo: {'bar': 1} is not valid under any of the given schemas"
    )

    s2 = strip_ansi(text_reporter._format_validation_error_message(err))
    assert s2 == "$.foo: {'bar': 1} is not valid under any of the given schemas"


def test_print_validation_error_nested(capsys, text_reporter):
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

    text_reporter._show_validation_error("foo.json", err, show_all_errors=True)
    captured = capsys.readouterr()
    # nothing to stderr
    assert captured.err == ""
    out = strip_ansi(captured.out)

    # only assert part of the message
    # dict member order isn't guaranteed and isn't relevant here
    assert "is not valid under any of the given schemas" in out
    assert "Underlying errors" in out
    assert "$.bar: {'baz': 'buzz'} is not of type 'string'" in out
    assert "$.bar.baz: 'buzz' is not of type 'integer'" in out
