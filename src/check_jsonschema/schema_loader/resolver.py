from __future__ import annotations

import typing as t

import click
import jsonschema


class _CliRefResolver(jsonschema.RefResolver):
    def resolve_remote(self, uri: str) -> t.Any:
        if uri.endswith(".yaml") or uri.endswith(".yml"):
            click.secho(
                """\
WARNING: You appear to be using a schema which references a YAML file.

This is not supported by check-jsonschema and may result in errors.
""",
                err=True,
                fg="yellow",
            )
        elif uri.endswith(".json5"):
            click.secho(
                """\
WARNING: You appear to be using a schema which references a JSON5 file.

This is not supported by check-jsonschema and may result in errors.
""",
                err=True,
                fg="yellow",
            )
        return super().resolve_remote(uri)


def make_ref_resolver(
    schema_uri: str | None, schema: dict
) -> jsonschema.RefResolver | None:
    if not schema_uri:
        return None

    base_uri = schema.get("$id", schema_uri)
    # FIXME: temporary type-ignore because typeshed has the type wrong
    return _CliRefResolver(base_uri, schema)  # type: ignore[arg-type]
