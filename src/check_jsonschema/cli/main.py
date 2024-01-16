from __future__ import annotations

import sys
import warnings

from .commands import main_command
from .legacy import legacy_main

_KNOWN_SUBCOMMANDS: frozenset[str] = frozenset(
    (
        "local",
        "remote",
        "vendored",
        "metaschema",
    )
)


def main(*, argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv

    if argv[1] not in _KNOWN_SUBCOMMANDS:
        warnings.warn(
            "This usage was detected to use the legacy command invocation. "
            "Upgrade to the new usage by following the upgrading guide: "
            "https://check-jsonschema.readthedocs.io/en/stable/upgrading.html",
            stacklevel=1,
        )
        legacy_main(argv[1:])
    else:
        main_command(argv[1:])
