pre-commit Usage
================

``check-jsonschema`` is designed to seamlessly integrate into your workflow as
a `pre-commit <https://pre-commit.com>`_ hook.

Supported Hooks
---------------

``check-jsonschema``
~~~~~~~~~~~~~~~~~~~~

Validate JSON or YAML files against a jsonschema on disk or fetched via HTTP(S).
You must specify a schema using pre-commit ``args`` configuration.

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-jsonschema
          files: ^data/.*\.json$
          args: ["--schemafile", "schemas/foo.json"]


``check-metaschema``
~~~~~~~~~~~~~~~~~~~~

Validate JSON Schema files against their matching metaschema, as specified in their
``"$schema"`` key.

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-metaschema
          files: ^schemas/.*\.json$


.. generated-hook-list-start


``check-azure-pipelines``
~~~~~~~~~~~~~~~~~~~~~~~~~

Validate Azure Pipelines config against the schema provided by Microsoft

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-azure-pipelines


``check-bamboo-spec``
~~~~~~~~~~~~~~~~~~~~~

Validate Bamboo Specs against the schema provided by SchemaStore

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-bamboo-spec


``check-bitbucket-pipelines``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate Bitbucket Pipelines against the schema provided by SchemaStore

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-bitbucket-pipelines


``check-buildkite``
~~~~~~~~~~~~~~~~~~~

Validate Buildkite Pipelines against the schema provided by Buildkite

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-buildkite


``check-dependabot``
~~~~~~~~~~~~~~~~~~~~

Validate Dependabot Config (v2) against the schema provided by SchemaStore

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-dependabot


``check-drone-ci``
~~~~~~~~~~~~~~~~~~

Validate Drone-CI Config against the schema provided by SchemaStore

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-drone-ci


``check-github-actions``
~~~~~~~~~~~~~~~~~~~~~~~~

Validate GitHub Actions against the schema provided by SchemaStore

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-github-actions


``check-github-workflows``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate GitHub Workflows against the schema provided by SchemaStore

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-github-workflows


``check-gitlab-ci``
~~~~~~~~~~~~~~~~~~~

Validate GitLab CI config against the schema provided by SchemaStore

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-gitlab-ci


``check-readthedocs``
~~~~~~~~~~~~~~~~~~~~~

Validate ReadTheDocs config against the schema provided by ReadTheDocs

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-readthedocs


``check-renovate``
~~~~~~~~~~~~~~~~~~

Validate Renovate config against the schema provided by Renovate (does not support renovate config in package.json)

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-renovate


``check-travis``
~~~~~~~~~~~~~~~~

Validate Travis Config against the schema provided by SchemaStore

.. code-block:: yaml
    :caption: example config

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-travis


.. generated-hook-list-end


Example Usages
--------------

Reimplement check-github-workflows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

   This behaves slightly differently from ``check-github-workflows`` and is not
   recommended. It is here only to demonstrate how ``--schemafile`` can be used.

The ``check-jsonschema`` hook can run any JSON Schema against a
file or set of files. For example, to implement the GitHub workflow check
manually, you could do this:

.. code-block:: yaml

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-jsonschema
          name: "Check GitHub Workflows"
          files: ^\.github/workflows/[^/]+$
          types: [yaml]
          args: ["--schemafile", "https://json.schemastore.org/github-workflow"]

Check a builtin schema
~~~~~~~~~~~~~~~~~~~~~~

``check-jsonschema`` packages some builtin schemas for implementing checks.

To check with the builtin schema that a GitHub workflow sets
``timeout-minutes`` on all jobs:

.. code-block:: yaml

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.24.1
      hooks:
        - id: check-jsonschema
          name: "Check GitHub Workflows set timeout-minutes"
          files: ^\.github/workflows/[^/]+$
          types: [yaml]
          args: ["--builtin-schema", "github-workflows-require-timeout"]
