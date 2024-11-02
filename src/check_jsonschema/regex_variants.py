import enum
import re
import typing as t

import jsonschema
import regress


class RegexVariantName(enum.Enum):
    default = "default"
    python = "python"


class _ConcreteImplementation(t.Protocol):
    def check_format(self, instance: t.Any) -> bool: ...

    def pattern_keyword(
        self, validator: t.Any, pattern: str, instance: str, schema: t.Any
    ) -> t.Iterator[jsonschema.ValidationError]: ...


class RegexImplementation:
    """
    A high-level interface for getting at the different possible
    implementations of regex behaviors.
    """

    _real_implementation: _ConcreteImplementation

    def __init__(self, variant: RegexVariantName) -> None:
        self.variant = variant

        if self.variant == RegexVariantName.default:
            self._real_implementation = _RegressImplementation()
        else:
            self._real_implementation = _PythonImplementation()

        self.check_format = self._real_implementation.check_format
        self.pattern_keyword = self._real_implementation.pattern_keyword


class _RegressImplementation:
    def check_format(self, instance: t.Any) -> bool:
        if not isinstance(instance, str):
            return True
        try:
            regress.Regex(instance)
        # something is wrong with RegressError getting into the published types
        # needs investigation... for now, ignore the error
        except regress.RegressError:  # type: ignore[attr-defined]
            return False
        return True

    def pattern_keyword(
        self, validator: t.Any, pattern: str, instance: str, schema: t.Any
    ) -> t.Iterator[jsonschema.ValidationError]:
        if not validator.is_type(instance, "string"):
            return

        try:
            regress_pattern = regress.Regex(pattern)
        except regress.RegressError:  # type: ignore[attr-defined]
            yield jsonschema.ValidationError(f"pattern {pattern!r} failed to compile")
        if not regress_pattern.find(instance):
            yield jsonschema.ValidationError(f"{instance!r} does not match {pattern!r}")


class _PythonImplementation:
    def check_format(self, instance: t.Any) -> bool:
        if not isinstance(instance, str):
            return True
        try:
            re.compile(instance)
        except re.error:
            return False
        return True

    def pattern_keyword(
        self, validator: t.Any, pattern: str, instance: str, schema: t.Any
    ) -> t.Iterator[jsonschema.ValidationError]:
        if not validator.is_type(instance, "string"):
            return

        try:
            re_pattern = re.compile(pattern)
        except re.error:
            yield jsonschema.ValidationError(f"pattern {pattern!r} failed to compile")
        if not re_pattern.search(instance):
            yield jsonschema.ValidationError(f"{instance!r} does not match {pattern!r}")
