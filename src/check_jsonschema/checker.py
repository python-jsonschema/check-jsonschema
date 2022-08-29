from __future__ import annotations

import typing as t

import click
import jsonschema

from . import utils
from .formats import FormatOptions
from .instance_loader import InstanceLoader
from .parsers import ParseError
from .reporter import Reporter
from .result import CheckResult
from .schema_loader import SchemaLoaderBase, SchemaParseError, UnsupportedUrlScheme


class _Exit(Exception):
    def __init__(self, code: int):
        self.code = code


class SchemaChecker:
    def __init__(
        self,
        schema_loader: SchemaLoaderBase,
        instance_loader: InstanceLoader,
        reporter: Reporter,
        *,
        format_opts: FormatOptions | None = None,
        traceback_mode: str = "short",
    ):
        self._schema_loader = schema_loader
        self._instance_loader = instance_loader
        self._reporter = reporter

        self._format_opts = format_opts if format_opts is not None else FormatOptions()
        self._traceback_mode = traceback_mode

    def _fail(self, msg: str, err: Exception | None = None) -> t.NoReturn:
        click.echo(msg, err=True)
        if err is not None:
            utils.print_error(err, mode=self._traceback_mode)
        raise _Exit(1)

    def get_validator(
        self, filename: str, doc: dict[str, t.Any]
    ) -> jsonschema.Validator:
        try:
            return self._schema_loader.get_validator(filename, doc, self._format_opts)
        except SchemaParseError as e:
            self._fail("Error: schemafile could not be parsed as JSON", e)
        except jsonschema.SchemaError as e:
            self._fail(f"Error: schemafile was not valid: {e}\n", e)
        except UnsupportedUrlScheme as e:
            self._fail(f"Error: {e}\n", e)
        except Exception as e:
            self._fail("Error: Unexpected Error building schema validator", e)

    def _build_result(self) -> CheckResult:
        result = CheckResult()
        for filename, data in self._instance_loader.iter_files():
            if isinstance(data, ParseError):
                result.record_parse_error(filename, data)
            else:
                validator = self.get_validator(filename, data)
                for err in validator.iter_errors(data):
                    result.record_validation_error(filename, err)
        return result

    def _run(self) -> None:
        try:
            result = self._build_result()
        except jsonschema.RefResolutionError as e:
            self._fail("Failure resolving $ref within schema\n", e)

        self._reporter.report_result(result)
        if not result.success:
            raise _Exit(1)

    def run(self) -> int:
        try:
            self._run()
        except _Exit as e:
            return e.code
        return 0
