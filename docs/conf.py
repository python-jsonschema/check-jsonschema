import datetime
import importlib.metadata

project = "check-jsonschema"
copyright = f"2021-{datetime.datetime.today().strftime('%Y')}, Stephen Rosen"
author = "Stephen Rosen"

# The full version, including alpha/beta/rc tags
release = importlib.metadata.version("check_jsonschema")

extensions = ["sphinx_issues"]
issues_github_path = "python-jsonschema/check-jsonschema"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build"]

# HTML theme options
html_theme = "furo"
pygments_style = "friendly"
pygments_dark_style = "monokai"  # this is a furo-specific option
