import sys
import typing as t

import jsonschema

from . import utils
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


def make_ref_resolver(schema_uri: str, schema: dict) -> jsonschema.RefResolver:
    base_uri = schema.get("$id", schema_uri)
    return jsonschema.RefResolver(base_uri, schema)


def make_validator(schema_uri: str, schema: dict, format_enabled: bool):
    # format checker (which may be None)
    format_checker = jsonschema.FormatChecker() if format_enabled else None

    # ref resolver which may be built from the schema path
    # if the location is a URL, there's no change, but if it's a file path
    # it's made absolute and URI-ized
    # the resolver should use `$id` if there is one present in the schema
    ref_resolver = make_ref_resolver(schema_uri, schema)

    # get the correct validator class and check the schema under its metaschema
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)

    # now that we know it's safe to try to create the validator instance, do it
    validator = validator_cls(
        schema,
        resolver=ref_resolver,
        format_checker=format_checker,
    )
    return validator


class SchemaChecker:
    def __init__(
        self,
        schemafile: str,
        instancefiles: t.List[str],
        *,
        cache_filename: t.Optional[str] = None,
        disable_cache: bool = False,
        format_enabled: bool = True,
        default_instance_filetype: t.Optional[str] = None,
        traceback_mode: str = "short",
    ):
        self._schemafile = schemafile
        self._instancefiles = instancefiles

        self._cache_filename = cache_filename
        self._disable_cache = disable_cache
        self._format_enabled = format_enabled
        self._default_instance_filetype = default_instance_filetype
        self._traceback_mode = traceback_mode

    def _fail(self, msg: str, err: t.Optional[Exception] = None) -> t.NoReturn:
        print(msg, file=sys.stderr)
        if err is not None:
            utils.print_error(err, mode=self._traceback_mode)
        sys.exit(1)

    def get_validator(self):
        schema_loader = SchemaLoader(
            self._schemafile,
            self._cache_filename,
            self._disable_cache,
        )
        try:
            return make_validator(
                schema_loader.get_schema_ref_base(),
                schema_loader.get_schema(),
                self._format_enabled,
            )
        except SchemaParseError:
            self._fail("Error: schemafile could not be parsed as JSON")
        except jsonschema.SchemaError as e:
            self._fail(f"Error: schemafile was not valid: {e}\n", e)

    def _build_error_map(self, validator, instance_loader):
        errors = {}
        for filename, doc in instance_loader.iter_files():
            for err in validator.iter_errors(doc):
                if filename not in errors:
                    errors[filename] = []
                errors[filename].append(err)
        return errors

    def run(self):
        validator = self.get_validator()

        instances = InstanceLoader(
            self._instancefiles, default_filetype=self._default_instance_filetype
        )

        try:
            errors = self._build_error_map(validator, instances)
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
