Optional Parsers
================

``check-jsonschema`` comes with out-of-the-box support for the JSON and YAML file
formats. Additional optional parsers may be installed, and are supported when
present.

JSON5
-----

- Supported for Instances: yes
- Supported for Schemas: yes

In order to support JSON5 files, either the ``pyjson5`` or ``json5`` package must
be installed.

In ``pre-commit-config.yaml``, this can be done with ``additional_dependencies``.
For example,

.. code-block:: yaml

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.27.2
      hooks:
        - id: check-renovate
          additional_dependencies: ['pyjson5']

TOML
----

- Supported for Instances: yes
- Supported for Schemas: no

In order to support TOML files, the ``tomli`` package must be installed.

In ``pre-commit-config.yaml``, this can be done with ``additional_dependencies``.
For example,

.. code-block:: yaml

    - repo: https://github.com/python-jsonschema/check-jsonschema
      rev: 0.27.2
      hooks:
        - id: check-jsonschema
          name: 'Check GitHub Workflows'
          files: ^mydata/
          types_or: [toml]
          args: ['--schemafile', 'schemas/toml-data.json']
          additional_dependencies: ['tomli']

The TOML format has support for dates and times as first-class types, meaning
that they are parsed as part of the data format.

``check-jsonschema`` will convert the parsed data back into strings so that they
can be checked by a schema. In general, the string conversion should be
checkable using ``"format": "date-time"``, ``"format": "date"``, and
``"format": "time"``.
