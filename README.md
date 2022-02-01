# check-jsonschema

A pre-commit hook for checking files against a [JSONSchema](https://json-schema.org/), built using the python [jsonschema](https://github.com/Julian/jsonschema/) package.
The schema may be specified as a local or remote (HTTP or HTTPS) file.

Remote files are automatically downloaded and cached if possible.

## Supported Hooks

The most generic hook is this one:

- check-jsonschema:
    Validate JSON or YAML files against a jsonschema on disk or fetched via HTTP(S)

These hooks check known files against schemas provided by Schemastore:

- check-github-workflows:
    Validate GitHub Workflows in `.github/workflows/`

- check-github-actions:
    Validate GitHub Actions in `.github/actions/` or the `action.yml` at the
    repo root

- check-travis: Validate Travis config

These hooks check known files against schemas provided by other sources:

- check-azure-pipelines:
    Validate Azure Pipelines config against the schema provided by Microsoft

- check-readthedocs:
    Validate ReadTheDocs yaml config against the schema provided by ReadTheDocs

- check-renovate:
    Validate RenovateBot config against the schema provided by Renovate (does
    not support config in package.json or JSON5)

## Example Usage

### Validate GitHub Workflows with Schemastore

You can use the schemastore github workflow schema to lint your GitHub workflow
files. All you need to add to your `.pre-commit-config.yaml` is this:

```yaml
- repo: https://github.com/sirosen/check-jsonschema
  rev: 0.10.1
  hooks:
    - id: check-github-workflows
```

### Applying an arbitrary schema to files

There is a more general hook available for running any jsonschema against a
file or set of files. For example, to implement the GitHub workflow check
manually, you could do this:

```yaml
- repo: https://github.com/sirosen/check-jsonschema
  rev: 0.10.1
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
- repo: https://github.com/sirosen/check-jsonschema
  rev: 0.10.1
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

This option is required unless `--builtin-schema` is used.

### `--no-cache`

Do not cache HTTP(S) downloaded schemas.

### `--disable-format`

JSON Schema defines a `"format"` attribute for string fields but does not require
that any validation for formats be applied.

Starting in version 0.6.0, `check-jsonschema` will automatically check some
formats by default.
This flag disables these checks.

Because `"format"` checking is not done by all JSON Schema tools, it is
possible that a file may validate under a schema with a different tool, but
fail with `check-jsonschema` if `--disable-format` is not set.

### `--format-regex`

Set a mode for handling of the `"regex"` value for `"format"`. The modes are as
follows:

mode | description
---|---
disabled | Skip checking `regex`, but leave other formats enabled.
default | Check for known non-python regex syntaxes. If one is found, the expression always passes. Otherwise, check validity in the python engine.
python | Require the regex to be valid in python regex syntax.

### `--cache-filename`

The name to use for caching a remote (HTTP or HTTPS) schema.

Defaults to using the last slash-delimited part of the URI.

### `--default-filetype`

The default filetype to assume on instance files when they are detected neither
as JSON nor as YAML.

For example, pass `--default-filetype yaml` to instruct that files which have
no extension should be treated as YAML.

By default, this is not set and files without a detected type of JSON or YAML
will fail.

### `--builtin-schema`

The name of a builtin schema from `check-jsonschema` to use.
Use of this option replaces `--schemafile`, and the two are mutually exclusive.

The following values are valid and refer to vendored copies of schemastore
schemas:

- `vendor.azure-pipelines`
- `vendor.github-actions`
- `vendor.github-workflows`
- `vendor.travis`
- `vendor.readthedocs`
- `vendor.renovate`

The following values are valid and refer to custom schemas:

- `github-workflows-require-timeout` -- This schema checks that a GitHub
  workflow explicitly sets `timeout-minutes` on all jobs. (The default value
  for this is 6 hours.)

### `--failover-builtin-schema`

Specify one of the `vendor` schemas which should be used if fetching
`--schemafile` fails.

For example, to download the latest `travis` schema, but failover to the
vendored copy, use
```bash
check-jsonschema --schemafile "https://json.schemastore.org/travis" --failover-builtin-schema vendor.travis
```

This is what is used by the hooks provided by `check-jsonschema`.
