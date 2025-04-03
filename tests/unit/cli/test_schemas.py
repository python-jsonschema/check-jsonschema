import jsonschema
import pytest

from check_jsonschema.builtin_schemas import get_builtin_schema
from check_jsonschema.cli.main_command import BUILTIN_SCHEMA_NAMES
from check_jsonschema.regex_variants import RegexImplementation, RegexVariantName
from check_jsonschema.schema_loader.main import _check_schema


@pytest.mark.parametrize("name", BUILTIN_SCHEMA_NAMES)
def test_check_schema_builtin(name):
    """
    Test that the buildin schema is valid
    """
    if name == "vendor.compose-spec":
        pytest.skip("vendor.compose-spec does not work")
        return
    regex_name = RegexVariantName.nonunicode if "azure-pipelines" in name else RegexVariantName.default
    regex_impl = RegexImplementation(regex_name)
    schema = get_builtin_schema(name)

    # get the correct validator class and check the schema under its metaschema
    validator_cls = jsonschema.validators.validator_for(schema)
    _check_schema(validator_cls, schema, regex_impl=regex_impl)
