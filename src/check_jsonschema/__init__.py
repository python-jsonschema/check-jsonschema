from .checker import SchemaChecker
from .loaders import instance_loader_from_args, schema_loader_from_args
from .parse_cli import parse_args


def main(cli_args=None):
    args = parse_args(cli_args)

    schema_loader = schema_loader_from_args(args)

    instance_loader = instance_loader_from_args(args)

    checker = SchemaChecker(
        schema_loader,
        instance_loader,
        format_enabled=not args.disable_format,
        traceback_mode=args.traceback_mode,
    )
    checker.run()

    print("ok -- validation done")
