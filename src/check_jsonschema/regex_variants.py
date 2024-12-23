import enum
import re
import typing as t

import jsonschema
import regress


class RegexVariantName(enum.Enum):
    default = "default"
    nonunicode = "nonunicode"
    python = "python"


class _ConcreteImplementation(t.Protocol):
    def check_format(self, instance: t.Any) -> bool: ...

    def pattern_keyword(
        self, validator: t.Any, pattern: str, instance: str, schema: t.Any
    ) -> t.Iterator[jsonschema.ValidationError]: ...

    def patternProperties_keyword(
        self,
        validator: t.Any,
        patternProperties: dict[str, t.Any],
        instance: dict[str, t.Any],
        schema: t.Any,
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
            self._real_implementation = _UnicodeRegressImplementation()
        elif self.variant == RegexVariantName.nonunicode:
            self._real_implementation = _NonunicodeRegressImplementation()
        else:
            self._real_implementation = _PythonImplementation()

        self.check_format = self._real_implementation.check_format
        self.pattern_keyword = self._real_implementation.pattern_keyword
        self.patternProperties_keyword = (
            self._real_implementation.patternProperties_keyword
        )


class _UnicodeRegressImplementation:
    def check_format(self, instance: t.Any) -> bool:
        if not isinstance(instance, str):
            return True
        try:
            regress.Regex(instance, flags="u")
        except regress.RegressError:
            return False
        return True

    def pattern_keyword(
        self, validator: t.Any, pattern: str, instance: str, schema: t.Any
    ) -> t.Iterator[jsonschema.ValidationError]:
        if not validator.is_type(instance, "string"):
            return

        try:
            regress_pattern = regress.Regex(pattern, flags="u")
        except regress.RegressError:
            yield jsonschema.ValidationError(f"pattern {pattern!r} failed to compile")
        if not regress_pattern.find(instance):
            yield jsonschema.ValidationError(f"{instance!r} does not match {pattern!r}")

    def patternProperties_keyword(
        self,
        validator: t.Any,
        patternProperties: dict[str, t.Any],
        instance: dict[str, t.Any],
        schema: t.Any,
    ) -> t.Iterator[jsonschema.ValidationError]:
        if not validator.is_type(instance, "object"):
            return

        for pattern, subschema in patternProperties.items():
            regress_pattern = regress.Regex(pattern, flags="u")
            for k, v in instance.items():
                if regress_pattern.find(k):
                    yield from validator.descend(
                        v,
                        subschema,
                        path=k,
                        schema_path=pattern,
                    )


class _NonunicodeRegressImplementation:
    def check_format(self, instance: t.Any) -> bool:
        if not isinstance(instance, str):
            return True
        try:
            regress.Regex(instance)
        except regress.RegressError:
            return False
        return True

    def pattern_keyword(
        self, validator: t.Any, pattern: str, instance: str, schema: t.Any
    ) -> t.Iterator[jsonschema.ValidationError]:
        if not validator.is_type(instance, "string"):
            return

        try:
            regress_pattern = regress.Regex(pattern)
        except regress.RegressError:
            yield jsonschema.ValidationError(f"pattern {pattern!r} failed to compile")
        if not regress_pattern.find(instance):
            yield jsonschema.ValidationError(f"{instance!r} does not match {pattern!r}")

    def patternProperties_keyword(
        self,
        validator: t.Any,
        patternProperties: dict[str, t.Any],
        instance: dict[str, t.Any],
        schema: t.Any,
    ) -> t.Iterator[jsonschema.ValidationError]:
        if not validator.is_type(instance, "object"):
            return

        for pattern, subschema in patternProperties.items():
            regress_pattern = regress.Regex(pattern)
            for k, v in instance.items():
                if regress_pattern.find(k):
                    yield from validator.descend(
                        v,
                        subschema,
                        path=k,
                        schema_path=pattern,
                    )


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

    def patternProperties_keyword(
        self,
        validator: t.Any,
        patternProperties: dict[str, t.Any],
        instance: dict[str, t.Any],
        schema: t.Any,
    ) -> t.Iterator[jsonschema.ValidationError]:
        if not validator.is_type(instance, "object"):
            return

        for pattern, subschema in patternProperties.items():
            for k, v in instance.items():
                if re.search(pattern, k):
                    yield from validator.descend(
                        v,
                        subschema,
                        path=k,
                        schema_path=pattern,
                    )
