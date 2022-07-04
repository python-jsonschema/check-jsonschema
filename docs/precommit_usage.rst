pre-commit Usage
================

``check-jsonschema`` is designed to seamlessly integrate into your workflow as
a `pre-commit <https://pre-commit.com>`_ hook.

Supported Hooks
---------------

The most generic hook is this one:

- ``check-jsonschema``:
    Validate JSON or YAML files against a jsonschema on disk or fetched via HTTP(S).
    You must specify a schema using pre-commit ``args`` configuration.

- ``check-metaschema``:
    Validate JSON Schema files against their matching metaschema, as specified in their
    ``"$schema"`` key

The following hooks check specific files against various schemas provided by
SchemaStore and other sources:

.. generated-hook-list-start

- ``check-azure-pipelines``:
    Validate Azure Pipelines config against the schema provided by Microsoft

- ``check-bamboo-spec``:
    Validate Bamboo Specs against the schema provided by SchemaStore

- ``check-dependabot``:
    Validate Dependabot Config (v2) against the schema provided by SchemaStore

- ``check-github-actions``:
    Validate GitHub Actions against the schema provided by SchemaStore

- ``check-github-workflows``:
    Validate GitHub Workflows against the schema provided by SchemaStore

- ``check-gitlab-ci``:
    Validate GitLab CI config against the schema provided by SchemaStore

- ``check-readthedocs``:
    Validate ReadTheDocs config against the schema provided by ReadTheDocs

- ``check-renovate``:
    Validate Renovate config against the schema provided by Renovate (does not support renovate config in package.json)

- ``check-travis``:
    Validate Travis Config against the schema provided by SchemaStore

.. generated-hook-list-end

Example Usage
-------------

Validate GitHub Workflows with Schemastore
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use the schemastore github workflow schema to lint your GitHub workflow
files. All you need to add to your ``.pre-commit-config.yaml`` is this:

.. code-block:: yaml

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.16.2
      hooks:
        - id: check-github-workflows

Applying an arbitrary schema to files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is a more general hook available for running any jsonschema against a
file or set of files. For example, to implement the GitHub workflow check
manually, you could do this:

.. code-block:: yaml

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.16.2
      hooks:
        - id: check-jsonschema
          name: "Check GitHub Workflows"
          files: ^\.github/workflows/
          types: [yaml]
          args: ["--schemafile", "https://json.schemastore.org/github-workflow"]

And to check with the builtin schema that a GitHub workflow sets
``timeout-minutes`` on all jobs:

.. code-block:: yaml

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.16.2
      hooks:
        - id: check-jsonschema
          name: "Check GitHub Workflows set timeout-minutes"
          files: ^\.github/workflows/
          types: [yaml]
          args: ["--builtin-schema", "github-workflows-require-timeout"]
