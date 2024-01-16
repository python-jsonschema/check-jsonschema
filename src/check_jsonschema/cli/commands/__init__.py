import click

from ..common_options import universal_opts


@click.group(
    "check-jsonschema",
    help="""\
Check files against a JSON Schema.
Supports JSON and YAML by default, and TOML and JSON5 when parsers are available.

Various modes of checking are supported via different subcommands.

'check-jsonschema' supports 'format' checks with appropriate libraries installed,
including the following formats by default:
    date, email, ipv4, ipv6, regex, uuid

Use `--disable-formats` to skip specific 'format' checks or all 'format' checking.
""",
)
@universal_opts
def main_command() -> None:
    raise NotImplementedError()
