import json
import os
import typing as t

import jsonschema
import ruamel.yaml
from identify import identify

from .cachedownloader import CacheDownloader

yaml = ruamel.yaml.YAML(typ="safe")


class SchemaParseError(ValueError):
    pass


class BadFileTypeError(ValueError):
    pass


class SchemaLoader:
    def __init__(
        self,
        schemafile: str,
        cache_filename: t.Optional[str] = None,
        disable_cache: bool = False,
    ):
        self._filename = os.path.expanduser(schemafile)
        if schemafile.startswith("https://") or schemafile.startswith("http://"):
            self._downloader = CacheDownloader(
                schemafile, cache_filename, disable_cache=disable_cache
            )
        else:
            self._downloader = None

    def _json_load(self, fp):
        try:
            return json.load(fp)
        except ValueError:
            raise SchemaParseError(self._filename)

    def get_validator(self):
        if self._downloader:
            with self._downloader.open() as fp:
                schema = self._json_load(fp)
        else:
            with open(self._filename) as f:
                schema = self._json_load(f)

        validator_cls = jsonschema.validators.validator_for(schema)

        validator_cls.check_schema(schema)
        validator = validator_cls(schema)
        return validator


class InstanceLoader:
    def __init__(self, filenames, default_filetype=None):
        self._filenames = filenames
        self._default_ft = default_filetype

    @property
    def _default_loadfunc(self):
        if not self._default_ft:
            return None
        if self._default_ft.lower() == "json":
            return json.load
        return yaml.load

    def iter_files(self):
        for fn in self._filenames:
            tags = identify.tags_from_path(fn)
            if "yaml" in tags:
                loadfunc = yaml.load
            elif "json" in tags:
                loadfunc = json.load
            else:
                loadfunc = self._default_loadfunc

            # TODO: handle this by storing it in the errors map
            if not loadfunc:
                raise BadFileTypeError(
                    f"cannot check {fn} as it is neither yaml nor json"
                )

            with open(fn) as fp:
                yield (fn, loadfunc(fp))
