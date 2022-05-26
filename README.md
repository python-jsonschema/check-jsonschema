[![pypi version](https://img.shields.io/pypi/v/check-jsonschema.svg)](https://pypi.org/project/check-jsonschema/)
[![supported pythons](https://img.shields.io/pypi/pyversions/check-jsonschema.svg)](https://pypi.org/project/check-jsonschema/)
[![build](https://github.com/python-jsonschema/check-jsonschema/actions/workflows/build.yaml/badge.svg)](https://github.com/python-jsonschema/check-jsonschema/actions/workflows/build.yaml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/python-jsonschema/check-jsonschema/main.svg)](https://results.pre-commit.ci/latest/github/python-jsonschema/check-jsonschema/main)


# check-jsonschema

A [pre-commit](https://pre-commit.com/) hook for checking files against a [JSONSchema](https://json-schema.org/), built using the python [jsonschema](https://github.com/Julian/jsonschema/) package.
The schema may be specified as a local or remote (HTTP or HTTPS) file.

Remote files are automatically downloaded and cached if possible.

## Supported Hooks

The most generic hook is this one:

- `check-jsonschema`:
    Validate JSON or YAML files against a jsonschema on disk or fetched via HTTP(S)

- `check-metaschema`:
    Validate JSON Schema files against their matching metaschema, as specified in their
    `"$schema"` key

The following hooks check specific files against various schemas provided by
SchemaStore and other sources:

<!-- generated-hook-list-start -->

- `check-azure-pipelines`:
    Validate Azure Pipelines config against the schema provided by Microsoft

- `check-bamboo-spec`:
    Validate Bamboo Specs against the schema provided by SchemaStore

- `check-dependabot`:
    Validate Dependabot Config (v2) against the schema provided by SchemaStore

- `check-github-actions`:
    Validate GitHub Actions against the schema provided by SchemaStore

- `check-github-workflows`:
    Validate GitHub Workflows against the schema provided by SchemaStore

- `check-gitlab-ci`:
    Validate GitLab CI config against the schema provided by SchemaStore

- `check-readthedocs`:
    Validate ReadTheDocs config against the schema provided by ReadTheDocs

- `check-renovate`:
    Validate Renovate config against the schema provided by Renovate (does not support renovate config in package.json)

- `check-travis`:
    Validate Travis Config against the schema provided by SchemaStore

<!-- generated-hook-list-end -->

## Example Usage

### Validate GitHub Workflows with Schemastore

You can use the schemastore github workflow schema to lint your GitHub workflow
files. All you need to add to your `.pre-commit-config.yaml` is this:

```yaml
- repo: https://github.com/python-jsonschema/check-jsonschema
  rev: 0.15.1
  hooks:
    - id: check-github-workflows
```

### Applying an arbitrary schema to files

There is a more general hook available for running any jsonschema against a
file or set of files. For example, to implement the GitHub workflow check
manually, you could do this:

```yaml
- repo: https://github.com/python-jsonschema/check-jsonschema
  rev: 0.15.1
  hooks:
    - id: check-jsonschema
      name: "Check GitHub Workflows"
      files: ^\.github/workflows/
      types: [yaml]
      args: ["--schemafile", "https://json.schemastore.org/github-workflow"]
```

And to check with the builtin schema that a GitHub workflow sets
`timeout-minutes` on all jobs:

```yaml
- repo: https://github.com/python-jsonschema/check-jsonschema
  rev: 0.15.1
  hooks:
    - id: check-jsonschema
      name: "Check GitHub Workflows set timeout-minutes"
      files: ^\.github/workflows/
      types: [yaml]
      args: ["--builtin-schema", "github-workflows-require-timeout"]
```

## Standalone Usage

You can also `pip install check-jsonschema` to run the tool manually.

For full usage info:

```bash
check-jsonschema --help
```

## CLI Options

These options apply both to standalone usage and pre-commit hook usage.

### `--schemafile`

The path or URL for a file containing a schema to use.

This option is required unless `--builtin-schema` or `--check-metaschema` is used.

### `--builtin-schema`

The name of a builtin schema from `check-jsonschema` to use.
Use of this option replaces `--schemafile`, and the two are mutually exclusive.

The following values are valid and refer to vendored copies schemas from
SchemaStore and other sources:

<!-- vendored-schema-list-start -->
- `vendor.azure-pipelines`
- `vendor.bamboo-spec`
- `vendor.dependabot`
- `vendor.github-actions`
- `vendor.github-workflows`
- `vendor.gitlab-ci`
- `vendor.readthedocs`
- `vendor.renovate`
- `vendor.travis`
<!-- vendored-schema-list-end -->

The following values refer to custom schemas:

- `github-workflows-require-timeout` -- This schema checks that a GitHub
  workflow explicitly sets `timeout-minutes` on all jobs. (The default value
  for this is 6 hours.)

### `--check-metaschema`

Validate each instancefile as a JSON Schema, using the relevant metaschema
defined in `"$schema"`.

This option replaces `--schemafile` and `--builtin-schema`, and these options
are mutually exclusive.

### `--default-filetype`

The default filetype to assume on instance files when they are detected neither
as JSON nor as YAML.

For example, pass `--default-filetype yaml` to instruct that files which have
no extension should be treated as YAML.

By default, this is not set and files without a detected type of JSON or YAML
will fail.

### `--data-transform`

`--data-transform` applies a transformation to instancefiles before they are
checked. The following transforms are supported:

- `azure-pipelines`:
    "Unpack" compile-time expressions for Azure Pipelines files, skipping them
    for the purposes of validation. This transformation is based on Microsoft's
    lanaguage-server for VSCode and how it handles expressions

### `-v`, `--verbose`

Request more output.

### `-q`, `--quiet`

Request less output.

### `-o`, `--output-format`

Use this option to choose how the output is presented. Either as `TEXT` (the
default) or `JSON`, as in `-o JSON`.

### Downloading and Caching Options

By default, when `--schemafile` is used to refer to an `http://` or `https://`
location, the schema is downloaded and cached based on the schema's
Last-Modified time. The following options control caching behaviors.

#### `--no-cache`

Disable caching. Do not cache downloaded schemas.

#### `--cache-filename`

The name to use for caching a remote schema.

Defaults to using the last slash-delimited part of the URI.

### "format" Validation Options

JSON Schema defines a `"format"` attribute for string fields but does not require
that any validation for formats be applied.

`check-jsonschema` supports checking several `"format"`s by default. The
following options can be used to control this behavior.

#### `--disable-format`

Disable all `"format"` checks.

Because `"format"` checking is not done by all JSON Schema tools, it is
possible that a file may validate under a schema with a different tool, but
fail with `check-jsonschema` if `--disable-format` is not set.

#### `--format-regex`

Set a mode for handling of the `"regex"` value for `"format"`. The modes are as
follows:

mode | description
---|---
disabled | Skip checking `regex`, but leave other formats enabled.
default | Check for known non-python regex syntaxes. If one is found, the expression always passes. Otherwise, check validity in the python engine.
python | Require the regex to be valid in python regex syntax.

### Error Handling Options

#### `--show-all-validation-errors`

Deprecated. Use `--verbose` instead.

#### `--traceback-mode`

By default, when an error is encountered, `check-jsonschema` will pretty-print
the error and exit.
Use `--traceback-mode full` to request the full traceback be printed, for
debugging and troubleshooting.

## Environment Variables

### `NO_COLOR`

Set `NO_COLOR=1` to explicitly turn off colorized output.

## Optional Parsers

`check-jsonschema` comes with out-of-the-box support for the JSON and YAML file
formats. Additional optional parsers may be installed, and are supported when
present.

### JSON5

In order to support JSON5 files, either the `pyjson5` or `json5` package must
be installed.

In `pre-commit-config.yaml`, this can be done with `additional_dependencies`.
For example,

```yaml
- repo: https://github.com/python-jsonschema/check-jsonschema
  rev: 0.15.1
  hooks:
    - id: check-renovate
      additional_dependencies: ['pyjson5']
```
