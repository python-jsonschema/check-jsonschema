import enum
import re
import typing as t

import jsonschema
import regress


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

    def pattern_keyword(
        self, validator: t.Any, pattern: str, instance: str, schema: t.Any
    ) -> t.Iterator[jsonschema.ValidationError]:
        if not validator.is_type(instance, "string"):
            return

        if self.variant == RegexVariantName.default:
            try:
                regress_pattern = regress.Regex(pattern)
            except regress.RegressError:  # type: ignore[attr-defined]
                yield jsonschema.ValidationError(
                    f"pattern {pattern!r} failed to compile"
                )
            if not regress_pattern.find(instance):
                yield jsonschema.ValidationError(
                    f"{instance!r} does not match {pattern!r}"
                )
        else:
            try:
                re_pattern = re.compile(pattern)
            except re.error:
                yield jsonschema.ValidationError(
                    f"pattern {pattern!r} failed to compile"
                )
            if not re_pattern.search(instance):
                yield jsonschema.ValidationError(
                    f"{instance!r} does not match {pattern!r}"
                )
