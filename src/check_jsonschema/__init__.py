import sys

from .checker import SchemaChecker
from .formats import FormatOptions
from .loaders import instance_loader_from_args, schema_loader_from_args
from .parse_cli import parse_args


def main(cli_args=None, *, exit=True):
    args = parse_args(cli_args)

    schema_loader = schema_loader_from_args(args)

    instance_loader = instance_loader_from_args(args)

    format_opts = FormatOptions(
        enabled=not args.disable_format, regex_behavior=args.format_regex
    )
    checker = SchemaChecker(
        schema_loader,
        instance_loader,
        format_opts=format_opts,
        traceback_mode=args.traceback_mode,
        show_all_errors=args.show_all_validation_errors,
    )
    ret = checker.run()
    if ret == 0:
        print("ok -- validation done")
    if exit:  # pragma: no cover
        sys.exit(ret)
    else:
        return ret
