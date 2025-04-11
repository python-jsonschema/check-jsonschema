import typing as t

import pytest

from check_jsonschema.cli import main as cli_main

click_type_test = pytest.importorskip(
    "click_type_test", reason="tests require 'click-type-test'"
)


def test_annotations_match_click_params():
    click_type_test.check_param_annotations(
        cli_main,
        overrides={
            # don't bother with a Literal for this, since it's relatively dynamic data
            "builtin_schema": str | None,
            # force default_filetype to be a Literal including `json5`, which is only
            # included in the choices if a parser is installed
            "default_filetype": t.Literal["json", "yaml", "toml", "json5"],
            "force_filetype": t.Literal["json", "yaml", "toml", "json5"] | None,
        },
    )
