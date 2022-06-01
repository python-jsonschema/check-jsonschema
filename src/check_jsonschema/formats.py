from __future__ import annotations

import copy
import enum
import re
import typing as t

import jsonschema

CHECKERS_BY_DIALECT = {
    "http://json-schema.org/draft-03/schema#": jsonschema.draft3_format_checker,
    "http://json-schema.org/draft-04/schema#": jsonschema.draft4_format_checker,
    "http://json-schema.org/draft-06/schema#": jsonschema.draft6_format_checker,
    "http://json-schema.org/draft-07/schema#": jsonschema.draft7_format_checker,
    "http://json-schema.org/draft-2019-09/schema": (
        jsonschema.draft201909_format_checker
    ),
    "http://json-schema.org/draft-2020-12/schema": (
        jsonschema.draft202012_format_checker
    ),
}
LATEST_DIALECT = "http://json-schema.org/draft-2020-12/schema"


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
    # map a schema's `$schema` attribute (the dialect / JSON Schema version) to a matching
    # format checker
    # default to the latest draft
    if schema_dialect is None or schema_dialect not in CHECKERS_BY_DIALECT:
        return CHECKERS_BY_DIALECT[LATEST_DIALECT]
    return CHECKERS_BY_DIALECT[schema_dialect]


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
