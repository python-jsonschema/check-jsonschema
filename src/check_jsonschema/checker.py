from __future__ import annotations

import sys
import typing as t

import jsonschema

from . import utils
from .formats import FormatOptions
from .loaders import (
    BadFileTypeError,
    InstanceLoader,
    SchemaLoaderBase,
    SchemaParseError,
    UnsupportedUrlScheme,
)


class _Exit(Exception):
    def __init__(self, code: int):
        self.code = code


class SchemaChecker:
    def __init__(
        self,
        schema_loader: SchemaLoaderBase,
        instance_loader: InstanceLoader,
        *,
        format_opts: FormatOptions | None = None,
        traceback_mode: str = "short",
        show_all_errors: bool = False,
    ):
        self._schema_loader = schema_loader
        self._instance_loader = instance_loader

        self._format_opts = format_opts if format_opts is not None else FormatOptions()
        self._traceback_mode = traceback_mode
        self._show_all_errors = show_all_errors

    def _fail(self, msg: str, err: Exception | None = None) -> t.NoReturn:
        print(msg, file=sys.stderr)
        if err is not None:
            utils.print_error(err, mode=self._traceback_mode)
        raise _Exit(1)

    def get_validator(self, filename: str, doc: dict[str, t.Any]):
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

    def _build_error_map(self):
        errors = {}
        for filename, doc in self._instance_loader.iter_files():
            validator = self.get_validator(filename, doc)
            for err in validator.iter_errors(doc):
                if filename not in errors:
                    errors[filename] = []
                errors[filename].append(err)
        return errors

    def _run(self) -> None:
        try:
            errors = self._build_error_map()
        except jsonschema.RefResolutionError as err:
            self._fail("Failure resolving $ref within schema\n", err)
        except BadFileTypeError as err:
            self._fail("Failure while loading instance files\n", err)

        if errors:
            print("Schema validation errors were encountered.")
            for filename, file_errors in errors.items():
                for err in file_errors:
                    utils.print_validation_error(
                        filename, err, show_all_errors=self._show_all_errors
                    )
            raise _Exit(1)

    def run(self) -> int:
        try:
            self._run()
        except _Exit as e:
            return e.code
        return 0
