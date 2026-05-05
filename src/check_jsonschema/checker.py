from __future__ import annotations

import pathlib
import typing as t

import click
import jsonschema
import referencing.exceptions

from . import format_errors
from .formats import FormatOptions
from .instance_loader import InstanceLoader, InstanceParseError
from .regex_variants import RegexImplementation
from .reporter import Reporter
from .result import CheckResult
from .schema_loader import SchemaLoaderBase, SchemaParseError, UnsupportedUrlScheme


class _Exit(Exception):
    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


class SchemaChecker:
    def __init__(
        self,
        schema_loader: SchemaLoaderBase,
        instance_loader: InstanceLoader,
        reporter: Reporter,
        *,
        format_opts: FormatOptions,
        regex_impl: RegexImplementation,
        traceback_mode: t.Literal["minimal", "short", "full"] = "short",
        fill_defaults: bool = False,
    ) -> None:
        self._schema_loader = schema_loader
        self._instance_loader = instance_loader
        self._reporter = reporter

        self._format_opts = format_opts
        self._regex_impl = regex_impl
        self._traceback_mode = traceback_mode
        self._fill_defaults = fill_defaults

    def _fail(self, msg: str, err: Exception | None = None) -> t.NoReturn:
        click.echo(msg, err=True)
        if err is not None:
            format_errors.print_error(err, mode=self._traceback_mode)
        raise _Exit(1)

    def _fail_ref_resolution(self, err: Exception) -> t.NoReturn:
        click.echo("Failure resolving $ref within schema", err=True)
        if self._traceback_mode == "full":
            format_errors.print_error(err, mode=self._traceback_mode)
        else:
            click.echo(f"  {_format_ref_resolution_error(err)}", err=True)
        raise _Exit(1)

    def get_validator(
        self,
        path: pathlib.Path | str,
        doc: t.Any,
        *,
        schemafile: str | None = None,
    ) -> jsonschema.protocols.Validator:
        try:
            return self._schema_loader.get_validator(
                path,
                doc,
                self._format_opts,
                self._regex_impl,
                self._fill_defaults,
                schemafile=schemafile,
            )
        except SchemaParseError as e:
            self._fail("Error: schemafile could not be parsed as JSON", e)
        except jsonschema.SchemaError as e:
            self._fail("Error: schemafile was not valid\n", e)
        except UnsupportedUrlScheme as e:
            self._fail(f"Error: {e}\n", e)
        except Exception as e:
            self._fail("Error: Unexpected Error building schema validator", e)

    def _build_result(self) -> CheckResult:
        result = CheckResult()
        for instance in self._instance_loader.iter_documents():
            if isinstance(instance, InstanceParseError):
                result.record_parse_error(instance.filename, instance.error)
            else:
                validator = self.get_validator(
                    instance.filename,
                    instance.data,
                    schemafile=instance.schemafile,
                )
                passing = True
                try:
                    validation_errors = validator.iter_errors(instance.data)
                    for err in validation_errors:
                        result.record_validation_error(instance.label, err)
                        passing = False
                except (
                    referencing.exceptions.NoSuchResource,
                    referencing.exceptions.Unretrievable,
                    referencing.exceptions.Unresolvable,
                ) as err:
                    result.record_validation_error(
                        instance.label, _make_ref_resolution_error(err)
                    )
                    passing = False
                if passing:
                    result.record_validation_success(instance.label)
        return result

    def _run(self) -> None:
        try:
            result = self._build_result()
        except (
            referencing.exceptions.NoSuchResource,
            referencing.exceptions.Unretrievable,
            referencing.exceptions.Unresolvable,
        ) as e:
            self._fail_ref_resolution(e)

        self._reporter.report_result(result)
        if not result.success:
            raise _Exit(1)

    def run(self) -> int:
        try:
            self._run()
        except _Exit as e:
            return e.code
        return 0


def _make_ref_resolution_error(err: Exception) -> jsonschema.ValidationError:
    return jsonschema.ValidationError(
        f"A $ref in the schema could not be resolved: "
        f"{_format_ref_resolution_error(err)}"
    )


def _format_ref_resolution_error(err: Exception) -> str:
    cause = err.__cause__ or err.__context__ or err
    if isinstance(cause, referencing.exceptions.PointerToNowhere):
        return (
            f"{type(cause).__name__}: {cause.ref!r} does not exist within "
            "the loaded schema."
        )
    if isinstance(cause, referencing.exceptions.NoSuchResource):
        return f"{type(cause).__name__}: could not retrieve {cause.ref!r}."
    if isinstance(cause, referencing.exceptions.Unretrievable):
        return f"{type(cause).__name__}: could not retrieve {cause.ref!r}."
    if isinstance(cause, referencing.exceptions.Unresolvable):
        ref = getattr(cause, "ref", None)
        if ref is not None:
            return f"{type(cause).__name__}: could not resolve {ref!r}."
    return format_errors.format_error_message(cause)
