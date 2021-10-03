import json
import os
import typing as t

import identify
import jsonschema
import ruamel.yaml

from .cachedownloader import CacheDownloader

yaml = ruamel.yaml.YAML(typ="safe")


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

    def get_validator(self):
        if self._downloader:
            with self._downloader.open() as fp:
                schema = json.load(fp)
        else:
            with open(self._filename) as f:
                schema = json.load(f)

        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema)
        return validator


class InstanceLoader:
    def __init__(self, filenames):
        self._filenames = filenames

    def iter_files(self):
        for fn in self._filenames:
            tags = identify.tags_from_path(fn)
            if "yaml" in tags:
                loadfunc = yaml.load
            elif "json" in tags:
                loadfunc = json.load
            else:
                # TODO: handle this by storing it in the errors map
                raise BadFileTypeError(
                    f"cannot check {fn} as it is neither yaml nor json"
                )
            with open(fn) as fp:
                yield (fn, loadfunc(fp))
