import enum
import re
import typing as t

import jsonschema


def _regex_check(instance):
    if not isinstance(instance, str):
        return True
    re.compile(instance)
    return True


def _gated_regex_check(instance):
    if not isinstance(instance, str):
        return True
    if re.search(r"\(\?[^!=]", instance):
        return True
    re.compile(instance)
    return True


class RegexFormatBehavior(enum.Enum):
    default = "default"
    disabled = "disabled"
    python = "python"


class FormatOptions:
    def __init__(
        self,
        *,
        enabled: bool = True,
        regex_behavior: RegexFormatBehavior = RegexFormatBehavior.default
    ):
        self.enabled = enabled
        self.regex_behavior = regex_behavior


def make_format_checker(
    opts: FormatOptions, draft: t.Optional[str] = None
) -> t.Optional[jsonschema.FormatChecker]:
    if not opts.enabled:
        return None

    formats = set(jsonschema.FormatChecker.checkers.keys())
    formats.remove("regex")
    checker = jsonschema.FormatChecker(formats=formats)

    if opts.regex_behavior == RegexFormatBehavior.disabled:
        pass
    elif opts.regex_behavior == RegexFormatBehavior.default:
        checker.checks("regex", raises=re.error)(_gated_regex_check)
    elif opts.regex_behavior == RegexFormatBehavior.python:
        checker.checks("regex", raises=re.error)(_regex_check)
    else:  # pragma: no cover
        raise NotImplementedError

    return checker
