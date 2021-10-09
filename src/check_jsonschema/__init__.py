from .checker import SchemaChecker
from .parse_cli import parse_args


def main():
    args = parse_args()
    checker = SchemaChecker(
        args.schemafile,
        args.instancefiles,
        cache_filename=args.cache_filename,
        disable_cache=args.no_cache,
        default_instance_filetype=args.default_filetype,
    )
    checker.run()
    print("ok -- validation done")
