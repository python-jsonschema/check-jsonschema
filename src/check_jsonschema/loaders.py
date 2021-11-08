import enum
import json
import pathlib
import typing as t
import urllib.parse

import jsonschema
import ruamel.yaml
from identify import identify

from .cachedownloader import CacheDownloader

yaml = ruamel.yaml.YAML(typ="safe")


class SchemaParseError(ValueError):
    pass


class BadFileTypeError(ValueError):
    pass


class UnsupportedUrlScheme(ValueError):
    pass


class SchemaLoaderMode(enum.Enum):
    cachedownloader = enum.auto()
    localpath = enum.auto()


class SchemaLoader:
    def __init__(
        self,
        schemafile: str,
        cache_filename: t.Optional[str] = None,
        disable_cache: bool = False,
        format_enabled: bool = True,
    ):
        # record input parameters (these are not to be modified)
        self._schemafile = schemafile
        self._cache_filename = cache_filename
        self._disable_cache = disable_cache
        self._format_enabled = format_enabled

        # parsed info (resolved paths, etc) gets initialized
        self._filename = schemafile
        self._url_info = urllib.parse.urlparse(schemafile)
        self._mode = self._determine_mode(self._url_info)

        # any complex construction (build a downloader object)
        self._downloader: t.Optional[CacheDownloader] = None
        if self._mode is SchemaLoaderMode.localpath:
            as_path = pathlib.Path(self._schemafile)
            self._filename = str(as_path.expanduser().resolve())
        elif self._mode is SchemaLoaderMode.cachedownloader:
            self._downloader = CacheDownloader(
                self._filename, self._cache_filename, disable_cache=self._disable_cache
            )

    def _determine_mode(self, url_info) -> SchemaLoaderMode:
        mode_map = {
            "http": SchemaLoaderMode.cachedownloader,
            "https": SchemaLoaderMode.cachedownloader,
            "file": SchemaLoaderMode.localpath,
            "": SchemaLoaderMode.localpath,
        }
        if url_info.scheme not in mode_map:
            raise UnsupportedUrlScheme(
                "check-jsonschema only supports http, https, and local files. "
                f"detected parsed URL had an unrecognized scheme: {self._url_info}"
            )
        return mode_map[url_info.scheme]

    def _json_load(self, fp):
        try:
            return json.load(fp)
        except ValueError:
            raise SchemaParseError(self._filename)

    def _read_schema(self):
        if self._mode is SchemaLoaderMode.localpath:
            with open(self._filename) as f:
                return self._json_load(f)
        elif self._mode is SchemaLoaderMode.cachedownloader:
            with self._downloader.open() as fp:
                return self._json_load(fp)
        else:  # pragma: no cover
            raise NotImplementedError  # unreachable

    def get_validator(self):
        schema = self._read_schema()
        format_checker = jsonschema.FormatChecker() if self._format_enabled else None
        base_uri = pathlib.Path(self._filename).resolve().as_uri()
        ref_resolver = (
            jsonschema.validators.RefResolver(base_uri=base_uri, referrer=schema)
            if self._filename
            else None
        )
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema, format_checker=format_checker)
        validator = validator_cls(
            schema, format_checker=format_checker, resolver=ref_resolver
        )
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
