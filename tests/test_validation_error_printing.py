import re

from jsonschema import Draft7Validator

from check_jsonschema import utils

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


def strip_ansi(text):
    return ANSI_ESCAPE.sub("", text)


def test_format_validation_error_message_simple():
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

    s1 = strip_ansi(utils.format_validation_error_message(err, filename="foo.json"))
    assert (
        s1 == "foo.json::$.foo: {'bar': 1} is not valid under any of the given schemas"
    )

    s2 = strip_ansi(utils.format_validation_error_message(err))
    assert s2 == "  $.foo: {'bar': 1} is not valid under any of the given schemas"


def test_print_validation_error_nested(capsys):
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

    utils.print_validation_error("foo.json", err, show_all_errors=True)
    captured = capsys.readouterr()
    # nothing to stdout
    assert captured.out == ""
    err = strip_ansi(captured.err)

    # only assert part of th message
    # dict member order isn't guaranteed and isn't relevant here
    assert "is not valid under any of the given schemas" in err
    assert "Underlying errors" in err
    assert "$.bar: {'baz': 'buzz'} is not of type 'string'" in err
    assert "$.bar.baz: 'buzz' is not of type 'integer'" in err
