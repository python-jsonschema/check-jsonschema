import os
import sys

PYTEST_LOADED = "pytest" in sys.modules

# this constant exists in service of the testsuite being able to forcibly disable the TOML
# loader
# the reason for this is that
#   - toml loading is enabled on py3.11+ with 'tomllib'
#   - on python < 3.11, toml loading is enabled with 'tomli'
#   - on python < 3.11, *coverage requires tomli*
#
# the end result is that it is not possible without special trickery to measure coverage
# in the disabled TOML state
# in order to measure coverage, we need 'tomli', so we will include this "magical" test
# constant in order to "forcibly" disable the 'tomli' usage
FORCE_TOML_DISABLED = False

if PYTEST_LOADED and os.getenv("FORCE_TOML_DISABLED") == "1":
    FORCE_TOML_DISABLED = True
