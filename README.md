# check-jsonschema

A pre-commit hook for checking files against a JSONSchema.
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

## Example Usage

### Validate GitHub Workflows with Schemastore

You can use the schemastore github workflow schema to lint your GitHub workflow
files. This hook is so useful, it's built in as a pre-set. All you need to add
to your `.pre-commit-config.yaml` is this:

```yaml
- repo: https://github.com/sirosen/check-jsonschema
  rev: 0.3.0
  hooks:
    - id: check-github-workflows
```

### Applying an arbitrary schema to files

There is a more general hook available for running any jsonschema against a
file or set of files. For example, to implement the GitHub workflow check
manually, you could do this:

```yaml
- repo: https://github.com/sirosen/check-jsonschema
  rev: 0.3.0
  hooks:
    - id: check-jsonschema
      name: "Check GitHub Workflows"
      language: python
      files: ^\.github/workflows/
      types: [yaml]
      args: ["--schemafile", "https://json.schemastore.org/github-workflow"]
```

## Standalone Usage

You can also `pip install check-jsonschema` to run the tool manually.

For full usage info:

```bash
check-jsonschema --help
```
