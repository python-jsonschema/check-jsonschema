import pytest

from check_jsonschema.parsers.yaml import ParseError, construct_yaml_implementation
from check_jsonschema.transforms.gitlab import (
    GITLAB_TRANSFORM,
    GitLabReferenceExpectationViolation,
)


def test_can_parse_yaml_with_transform():
    rawdata = """\
a: b
c: d
"""

    impl = construct_yaml_implementation()

    data = impl.load(rawdata)
    assert data == {"a": "b", "c": "d"}

    GITLAB_TRANSFORM.modify_yaml_implementation(impl)
    data = impl.load(rawdata)
    assert data == {"a": "b", "c": "d"}


def test_can_parse_ok_gitlab_yaml_with_transform():
    rawdata = """\
foo:
- !reference [bar, baz]
"""
    impl = construct_yaml_implementation()

    with pytest.raises(ParseError):
        data = impl.load(rawdata)

    GITLAB_TRANSFORM.modify_yaml_implementation(impl)
    data = impl.load(rawdata)
    assert data == {"foo": [["bar", "baz"]]}


def test_cannot_parse_bad_gitlab_yaml_with_transform():
    rawdata = """\
foo:
- !reference true
"""
    impl = construct_yaml_implementation()

    with pytest.raises(ParseError):
        impl.load(rawdata)

    GITLAB_TRANSFORM.modify_yaml_implementation(impl)
    with pytest.raises(
        GitLabReferenceExpectationViolation,
        match=r"check-jsonschema rejects this gitlab \!reference tag: .*",
    ):
        impl.load(rawdata)
