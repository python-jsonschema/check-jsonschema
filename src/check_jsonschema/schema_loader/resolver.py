from __future__ import annotations

import typing as t
import urllib.parse

import referencing
import requests
from referencing.jsonschema import DRAFT202012, Schema

from ..parsers import ParserSet
from ..utils import filename2path


def make_reference_registry(
    parsers: ParserSet, schema_uri: str | None, schema: dict
) -> referencing.Registry:
    schema_resource = referencing.Resource.from_contents(
        schema, default_specification=DRAFT202012
    )
    # mypy does not recognize that Registry is an `attrs` class and has `retrieve` as an
    # argument to its implicit initializer
    registry: referencing.Registry = referencing.Registry(  # type: ignore[call-arg]
        retrieve=create_retrieve_callable(parsers, schema_uri)
    )

    if schema_uri is not None:
        registry = registry.with_resource(uri=schema_uri, resource=schema_resource)

    id_attribute = schema.get("$id")
    if id_attribute is not None:
        registry = registry.with_resource(uri=id_attribute, resource=schema_resource)

    return registry


def create_retrieve_callable(
    parser_set: ParserSet, schema_uri: str | None
) -> t.Callable[[str], referencing.Resource[Schema]]:
    def get_local_file(uri: str) -> t.Any:
        path = filename2path(uri)
        return parser_set.parse_file(path, "json")

    def retrieve_reference(uri: str) -> referencing.Resource[Schema]:
        scheme = urllib.parse.urlsplit(uri).scheme
        if scheme == "" and schema_uri is not None:
            full_uri = urllib.parse.urljoin(schema_uri, uri)
        else:
            full_uri = uri

        full_uri_scheme = urllib.parse.urlsplit(full_uri).scheme
        if full_uri_scheme in ("http", "https"):
            data = requests.get(full_uri, stream=True)
            parsed_object = parser_set.parse_data_with_path(data.raw, full_uri, "json")
        else:
            parsed_object = get_local_file(full_uri)

        return referencing.Resource.from_contents(
            parsed_object, default_specification=DRAFT202012
        )

    return retrieve_reference
