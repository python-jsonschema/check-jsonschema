from __future__ import annotations

import enum
import re
import typing as t

import jsonschema


def _regex_check(instance: t.Any) -> bool:
    if not isinstance(instance, str):
        return True
    re.compile(instance)
    return True


def _gated_regex_check(instance: t.Any) -> bool:
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
        regex_behavior: RegexFormatBehavior = RegexFormatBehavior.default,
    ) -> None:
        self.enabled = enabled
        self.regex_behavior = regex_behavior


def make_format_checker(
    opts: FormatOptions, draft: str | None = None
) -> jsonschema.FormatChecker | None:
    if not opts.enabled:
        return None

    formats = set(jsonschema.FormatChecker.checkers.keys())
    formats.remove("regex")
    checker = jsonschema.FormatChecker(formats=formats)

    # FIXME: type-ignore comments to handle incorrect annotation
    # fixed in https://github.com/python/typeshed/pull/7990
    # once available, remove the ignores
    if opts.regex_behavior == RegexFormatBehavior.disabled:
        pass
    elif opts.regex_behavior == RegexFormatBehavior.default:
        checker.checks("regex", raises=re.error)(  # type: ignore[arg-type]
            _gated_regex_check
        )
    elif opts.regex_behavior == RegexFormatBehavior.python:
        checker.checks("regex", raises=re.error)(_regex_check)  # type: ignore[arg-type]
    else:  # pragma: no cover
        raise NotImplementedError

    return checker
