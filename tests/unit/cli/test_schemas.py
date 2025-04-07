import warnings

import jsonschema
import pytest

from check_jsonschema.builtin_schemas import get_builtin_schema
from check_jsonschema.cli.main_command import BUILTIN_SCHEMA_NAMES
from check_jsonschema.regex_variants import RegexImplementation, RegexVariantName
from check_jsonschema.schema_loader.main import _check_schema


@pytest.mark.parametrize("name", BUILTIN_SCHEMA_NAMES)
def test_check_schema_builtin(name):
    """
    Test that the builtin schema is valid
    """
    regex_name = RegexVariantName.default
    if "azure-pipelines" in name:
        regex_name = RegexVariantName.nonunicode
    elif name == "vendor.compose-spec":
        # supress DeprecationWarning: The metaschema specified by $schema was not found.
        # This is likely due to the schema being a draft-07 schema.
        warnings.filterwarnings("ignore", category=DeprecationWarning)
    regex_impl = RegexImplementation(regex_name)
    schema = get_builtin_schema(name)

    # get the correct validator class and check the schema under its metaschema
    validator_cls = jsonschema.validators.validator_for(schema)
    _check_schema(validator_cls, schema, regex_impl=regex_impl)
