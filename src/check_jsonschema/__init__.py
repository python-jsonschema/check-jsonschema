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
        traceback_mode=args.traceback_mode,
        failover_builtin_schema=args.failover_builtin_schema,
    )
    checker.run()
    print("ok -- validation done")
