from __future__ import annotations

import copy
import enum
import re
import typing as t

import jsonschema
import jsonschema.validators
import regress

from .implementations import validate_rfc3339

# all known format strings except for a selection from draft3 which have either
# been renamed or removed:
# - color
# - host-name
# - ip-address
KNOWN_FORMATS: tuple[str, ...] = (
    "date",
    "date-time",
    "duration",
    "email",
    "hostname",
    "idn-email",
    "idn-hostname",
    "ipv4",
    "ipv6",
    "iri",
    "iri-reference",
    "json-pointer",
    "regex",
    "relative-json-pointer",
    "time",
    "uri",
    "uri-reference",
    "uri-template",
    "uuid",
)


class RegexVariantName(enum.Enum):
    default = "default"
    python = "python"


class RegexImplementation:
    def __init__(self, variant: RegexVariantName) -> None:
        self.variant = variant

    def check_format(self, instance: t.Any) -> bool:
        if not isinstance(instance, str):
            return True

        try:
            if self.variant == RegexVariantName.default:
                regress.Regex(instance)
            else:
                re.compile(instance)
        # something is wrong with RegressError getting into the published types
        # needs investigation... for now, ignore the error
        except (regress.RegressError, re.error):  # type: ignore[attr-defined]
            return False

        return True


class FormatOptions:
    def __init__(
        self,
        *,
        enabled: bool = True,
        regex_variant: RegexVariantName = RegexVariantName.default,
        disabled_formats: tuple[str, ...] = (),
    ) -> None:
        self.enabled = enabled
        self.regex_variant = regex_variant
        self.disabled_formats = disabled_formats


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

    # replace the regex check
    del checker.checkers["regex"]
    regex_impl = RegexImplementation(opts.regex_variant)
    checker.checks("regex")(regex_impl.check_format)
    checker.checks("date-time")(validate_rfc3339)

    # remove the disabled checks, which may include the regex check
    for checkname in opts.disabled_formats:
        if checkname not in checker.checkers:
            continue
        del checker.checkers[checkname]

    return checker
