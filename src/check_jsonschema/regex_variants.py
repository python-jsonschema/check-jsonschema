import enum
import re
import typing as t

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
