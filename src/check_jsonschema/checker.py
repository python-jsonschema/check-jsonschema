import sys
import typing as t

import jsonschema

from .loaders import InstanceLoader, SchemaLoader, SchemaParseError


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
    ):
        self._schemafile = schemafile
        self._instancefiles = instancefiles

        self._cache_filename = cache_filename
        self._disable_cache = disable_cache
        self._format_enabled = format_enabled
        self._default_instance_filetype = default_instance_filetype

    def _fail(self, msg):
        print(msg)
        sys.exit(1)

    def get_validator(self):
        schema_loader = SchemaLoader(
            self._schemafile,
            self._cache_filename,
            self._disable_cache,
            self._format_enabled,
        )
        try:
            return schema_loader.get_validator()
        except SchemaParseError:
            self._fail("Error: schemafile could not be parsed as JSON")
        except jsonschema.SchemaError as e:
            self._fail(f"Error: schemafile was not valid: {e}")

    def run(self):
        validator = self.get_validator()

        instances = InstanceLoader(
            self._instancefiles, default_filetype=self._default_instance_filetype
        )

        failures = {}
        for filename, doc in instances.iter_files():
            try:
                validator.validate(instance=doc)
            except jsonschema.ValidationError as err:
                failures[filename] = err

        if failures:
            print("Schema validation errors were encountered.")
            for filename, err in failures.items():
                path = [str(x) for x in err.path] or ["<root>"]
                path = ".".join(x if "." not in x else f'"{x}"' for x in path)
                print(f"  \033[0;33m{filename}::{path}: \033[0m{err.message}")
            sys.exit(1)
