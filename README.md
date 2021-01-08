# check-jsonschema

A pre-commit hook for checking files against a JSONSchema.
The schema may be specified as a local or remote (HTTP or HTTPS) file.

Remote files are automatically downloaded and cached if possible.

## Example Usage: Validate GitHub Workflows with Schemastore

Add this hook to your pre-commit config:

```yaml
- repo: https://github.com/sirosen/check-jsonschema
  rev: 0.1.0
  hooks:
    - id: check-workflows
      name: "Lint GitHub Workflows"
      language: python
      files: ^\.github/workflows/.*\.yaml$
      args: ["--schemafile", "https://json.schemastore.org/github-workflow"]
```
