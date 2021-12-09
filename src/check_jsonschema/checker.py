import sys
import typing as t

import jsonschema

from . import utils
from .builtin_schemas import NoSuchSchemaError
from .loaders import InstanceLoader, SchemaLoader, SchemaParseError


def json_path(err: jsonschema.ValidationError) -> str:
    """
    This method is a backport of the json_path attribute provided by
    jsonschema.ValidationError for jsonschema v4.x

    It is needed until python3.6 is no longer supported by check-jsonschema,
    as jsonschema 4 dropped support for py36
    """
    path = "$"
    for elem in err.absolute_path:
        if isinstance(elem, int):
            path += "[" + str(elem) + "]"
        else:
            path += "." + elem
    return path


class SchemaChecker:
    def __init__(
        self,
        schema_loader: SchemaLoader,
        instance_loader: InstanceLoader,
        *,
        format_enabled: bool = True,
        traceback_mode: str = "short",
    ):
        self._schema_loader = schema_loader
        self._instance_loader = instance_loader

        self._format_enabled = format_enabled
        self._traceback_mode = traceback_mode

    def _fail(self, msg: str, err: t.Optional[Exception] = None) -> t.NoReturn:
        print(msg, file=sys.stderr)
        if err is not None:
            utils.print_error(err, mode=self._traceback_mode)
        sys.exit(1)

    def get_validator(self):
        try:
            return self._schema_loader.make_validator(self._format_enabled)
        except SchemaParseError:
            self._fail("Error: schemafile could not be parsed as JSON")
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

    def run(self):
        validator = self.get_validator()

        try:
            errors = self._build_error_map(validator)
        except jsonschema.RefResolutionError as err:
            self._fail("Failure resolving $ref within schema\n", err)

        if errors:
            print("Schema validation errors were encountered.")
            for filename, file_errors in errors.items():
                for err in file_errors:
                    print(
                        f"  \033[0;33m{filename}::{json_path(err)}: \033[0m{err.message}",
                        file=sys.stderr,
                    )
            sys.exit(1)
