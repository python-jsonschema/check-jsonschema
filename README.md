[![pypi version](https://img.shields.io/pypi/v/check-jsonschema.svg)](https://pypi.org/project/check-jsonschema/)
[![supported pythons](https://img.shields.io/pypi/pyversions/check-jsonschema.svg)](https://pypi.org/project/check-jsonschema/)
[![build](https://github.com/python-jsonschema/check-jsonschema/actions/workflows/build.yaml/badge.svg)](https://github.com/python-jsonschema/check-jsonschema/actions/workflows/build.yaml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/python-jsonschema/check-jsonschema/main.svg)](https://results.pre-commit.ci/latest/github/python-jsonschema/check-jsonschema/main)
[![readthedocs documentation](https://readthedocs.org/projects/check-jsonschema/badge/?version=stable&style=flat)](https://check-jsonschema.readthedocs.io/en/stable)


# check-jsonschema

A JSON Schema CLI and [pre-commit](https://pre-commit.com/) hook built on [jsonschema](https://github.com/python-jsonschema/jsonschema/).
The schema may be specified as a local or remote (HTTP or HTTPS) file.

Remote files are automatically downloaded and cached if possible.

## Usage

`check-jsonschema` can be installed and run as a CLI tool, or via pre-commit.

### Example pre-commit config

The following configuration uses `check-jsonschema` to validate Github Workflow
files.

```yaml
- repo: https://github.com/python-jsonschema/check-jsonschema
  rev: 0.23.0
  hooks:
    - id: check-github-workflows
```

## Documentation

Full documentation can be found at https://check-jsonschema.readthedocs.io/
