from __future__ import annotations

import typing as t
import urllib.parse

import referencing
import requests
from referencing.jsonschema import DRAFT202012, Schema

from ..parsers import ParserSet
from ..utils import filename2path


def make_reference_registry(
    parsers: ParserSet, retrieval_uri: str | None, schema: dict
) -> referencing.Registry:
    id_attribute_: t.Any = schema.get("$id")
    if isinstance(id_attribute_, str):
        id_attribute: str | None = id_attribute_
    else:
        id_attribute = None

    schema_resource = referencing.Resource.from_contents(
        schema, default_specification=DRAFT202012
    )
    # mypy does not recognize that Registry is an `attrs` class and has `retrieve` as an
    # argument to its implicit initializer
    registry: referencing.Registry = referencing.Registry(  # type: ignore[call-arg]
        retrieve=create_retrieve_callable(parsers, retrieval_uri, id_attribute)
    )

    if retrieval_uri is not None:
        registry = registry.with_resource(uri=retrieval_uri, resource=schema_resource)
    if id_attribute is not None:
        registry = registry.with_resource(uri=id_attribute, resource=schema_resource)

    return registry


def create_retrieve_callable(
    parser_set: ParserSet, retrieval_uri: str | None, id_attribute: str | None
) -> t.Callable[[str], referencing.Resource[Schema]]:
    base_uri = id_attribute
    if base_uri is None:
        base_uri = retrieval_uri

    cache = ResourceCache()

    def get_local_file(uri: str) -> t.Any:
        path = filename2path(uri)
        return parser_set.parse_file(path, "json")

    def retrieve_reference(uri: str) -> referencing.Resource[Schema]:
        scheme = urllib.parse.urlsplit(uri).scheme
        if scheme == "" and base_uri is not None:
            full_uri = urllib.parse.urljoin(base_uri, uri)
        else:
            full_uri = uri

        if full_uri in cache._cache:
            return cache[uri]

        full_uri_scheme = urllib.parse.urlsplit(full_uri).scheme
        if full_uri_scheme in ("http", "https"):
            data = requests.get(full_uri, stream=True)
            parsed_object = parser_set.parse_data_with_path(
                data.content, full_uri, "json"
            )
        else:
            parsed_object = get_local_file(full_uri)

        cache[uri] = parsed_object
        return cache[uri]

    return retrieve_reference


class ResourceCache:
    def __init__(self) -> None:
        self._cache: t.Dict[str, referencing.Resource[Schema]] = {}

    def __setitem__(self, uri: str, data: t.Any) -> referencing.Resource[Schema]:
        resource = referencing.Resource.from_contents(
            data, default_specification=DRAFT202012
        )
        self._cache[uri] = resource
        return resource

    def __getitem__(self, uri: str) -> referencing.Resource[Schema]:
        return self._cache[uri]

    def __contains__(self, uri: str) -> bool:
        return uri in self._cache
