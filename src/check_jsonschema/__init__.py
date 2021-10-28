from .checker import SchemaChecker
from .parse_cli import parse_args


def main(cli_args=None):
    args = parse_args(cli_args)
    checker = SchemaChecker(
        args.schemafile,
        args.instancefiles,
        cache_filename=args.cache_filename,
        disable_cache=args.no_cache,
        format_enabled=not args.disable_format,
        default_instance_filetype=args.default_filetype,
    )
    checker.run()
    print("ok -- validation done")
