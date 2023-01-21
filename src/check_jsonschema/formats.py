from __future__ import annotations

import copy
import enum
import re
import typing as t

import jsonschema
import jsonschema.validators


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


def get_base_format_checker(schema_dialect: str | None) -> jsonschema.FormatChecker:
    # resolve the dialect, if given, to a validator class
    # default to the latest draft
    validator_class = jsonschema.validators.validator_for(
        {} if schema_dialect is None else {"$schema": schema_dialect},
        default=jsonschema.Draft202012Validator,
    )
    return validator_class.FORMAT_CHECKER


def make_format_checker(
    opts: FormatOptions,
    schema_dialect: str | None = None,
) -> jsonschema.FormatChecker | None:
    if not opts.enabled:
        return None

    # copy the base checker
    base_checker = get_base_format_checker(schema_dialect)
    checker = copy.deepcopy(base_checker)

    # remove the regex check
    del checker.checkers["regex"]

    if opts.regex_behavior == RegexFormatBehavior.disabled:
        pass
    elif opts.regex_behavior == RegexFormatBehavior.default:
        checker.checks("regex", raises=re.error)(_gated_regex_check)
    elif opts.regex_behavior == RegexFormatBehavior.python:
        checker.checks("regex", raises=re.error)(_regex_check)
    else:  # pragma: no cover
        raise NotImplementedError

    return checker
