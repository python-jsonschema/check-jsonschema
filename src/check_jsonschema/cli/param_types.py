from __future__ import annotations

import functools
import importlib
import re
import typing as t

import click
import jsonschema
from click.shell_completion import CompletionItem

from check_jsonschema.file_wrapper import BinaryFileInput

C = t.TypeVar("C", bound=t.Callable[..., t.Any])


def _shim_click_8_2_get_metavar(func: C) -> C:
    @functools.wraps(func)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> None:
        if len(args) > 1 or "ctx" in kwargs:
            return func(*args, **kwargs)
        return func(*args, ctx=None, **kwargs)

    return wrapper  # type: ignore[return-value]


class CommaDelimitedList(click.ParamType):
    name = "comma_delimited"

    def __init__(
        self,
        *,
        convert_values: t.Callable[[str], str] | None = None,
        choices: t.Iterable[str] | None = None,
    ) -> None:
        super().__init__()
        self.convert_values = convert_values
        self.choices = list(choices) if choices is not None else None

    @_shim_click_8_2_get_metavar
    def get_metavar(self, param: click.Parameter, ctx: click.Context | None) -> str:
        if self.choices is not None:
            return "{" + ",".join(self.choices) + "}"
        return "TEXT,TEXT,..."

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> list[str]:
        value = super().convert(value, param, ctx)

        # if `--foo` is a comma delimited list and someone passes
        # `--foo ""`, take that as `foo=[]` rather than foo=[""]
        resolved = value.split(",") if value else []

        if self.convert_values is not None:
            resolved = [self.convert_values(x) for x in resolved]

        if self.choices is not None:
            bad_values = [x for x in resolved if x not in self.choices]
            if bad_values:
                self.fail(
                    f"the values {bad_values} were not valid choices",
                    param=param,
                    ctx=ctx,
                )

        return resolved


class ValidatorClassName(click.ParamType):
    name = "validator"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> type[jsonschema.protocols.Validator]:
        """
        Use a colon-based parse to split this up and do the import with importlib.
        This method is inspired by pkgutil.resolve_name and uses the newer syntax
        documented there.

        pkgutil supports both
            W(.W)*
        and
            W(.W)*:(W(.W)*)?
        as patterns, but notes that the first one is for backwards compatibility only.
        The second form is preferred because it clarifies the division between the
        importable name and any namespaced path to an object or class.

        As a result, only one import is needed, rather than iterative imports over the
        list of names.
        """
        value = super().convert(value, param, ctx)
        pattern = re.compile(
            r"^(?P<pkg>(?!\d)(\w+)(\.(?!\d)(\w+))*):"
            r"(?P<cls>(?!\d)(\w+)(\.(?!\d)(\w+))*)$"
        )
        m = pattern.match(value)
        if m is None:
            self.fail(
                f"'{value}' is not a valid specifier in '<package>:<class>' form",
                param,
                ctx,
            )
        pkg = m.group("pkg")
        classname = m.group("cls")
        try:
            result: t.Any = importlib.import_module(pkg)
        except ImportError as e:
            self.fail(f"'{pkg}' was not an importable module. {str(e)}", param, ctx)
        try:
            for part in classname.split("."):
                result = getattr(result, part)
        except AttributeError as e:
            self.fail(
                f"'{classname}' was not resolvable to a class in '{pkg}'. {str(e)}",
                param,
                ctx,
            )

        if not isinstance(result, type):
            self.fail(f"'{classname}' in '{pkg}' is not a class", param, ctx)

        return t.cast(t.Type[jsonschema.protocols.Validator], result)


class BinaryFileInputParam(click.ParamType[t.BinaryIO]):
    def shell_complete(
        self, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> list[CompletionItem]:
        return [CompletionItem(incomplete, type="file")]

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> t.BinaryIO:
        file = BinaryFileInput(value)
        if ctx is not None:
            ctx.call_on_close(file.close)
        file.check_can_open()
        # type checkers won't recognize a BinaryFileInput as a BinaryIO unless we do a
        # lot of extra work, because they don't follow that it uses `__getattr__` to
        # proxy everything to the underlying stream
        return file  # type: ignore[return-value]
