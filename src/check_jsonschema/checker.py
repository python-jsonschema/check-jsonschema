import sys
import typing as t

import jsonschema

from . import utils
from .builtin_schemas import NoSuchSchemaError
from .formats import FormatOptions
from .loaders import InstanceLoader, SchemaLoader, SchemaParseError


class _Exit(Exception):
    def __init__(self, code: int):
        self.code = code


class SchemaChecker:
    def __init__(
        self,
        schema_loader: SchemaLoader,
        instance_loader: InstanceLoader,
        *,
        format_opts: t.Optional[FormatOptions] = None,
        traceback_mode: str = "short",
        show_all_errors: bool = False,
    ):
        self._schema_loader = schema_loader
        self._instance_loader = instance_loader

        self._format_opts = format_opts if format_opts is not None else FormatOptions()
        self._traceback_mode = traceback_mode
        self._show_all_errors = show_all_errors

    def _fail(self, msg: str, err: t.Optional[Exception] = None) -> t.NoReturn:
        print(msg, file=sys.stderr)
        if err is not None:
            utils.print_error(err, mode=self._traceback_mode)
        raise _Exit(1)

    def get_validator(self):
        try:
            return self._schema_loader.make_validator(self._format_opts)
        except SchemaParseError as e:
            self._fail("Error: schemafile could not be parsed as JSON", e)
        except jsonschema.SchemaError as e:
            self._fail(f"Error: schemafile was not valid: {e}\n", e)
        except NoSuchSchemaError as e:
            self._fail("Error: builtin schema could not be loaded, no such schema\n", e)
        except Exception as e:
            self._fail("Error: Unexpected Error building schema validator", e)

    def _build_error_map(self, validator):
        errors = {}
        for filename, doc in self._instance_loader.iter_files():
            for err in validator.iter_errors(doc):
                if filename not in errors:
                    errors[filename] = []
                errors[filename].append(err)
        return errors

    def _run(self) -> None:
        validator = self.get_validator()

        try:
            errors = self._build_error_map(validator)
        except jsonschema.RefResolutionError as err:
            self._fail("Failure resolving $ref within schema\n", err)

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
