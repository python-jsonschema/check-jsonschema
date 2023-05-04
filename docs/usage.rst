Usage
=====

The ``check-jsonschema`` CLI requires that you specify a JSON Schema and a set of
instance files which are validated under that schema.

Typical usage is of the form

.. code-block:: bash

    check-jsonschema --schemafile ./foo-schema.json foo-instance1.json foo-instance2.json

Detailed helptext is always available interactively via

.. code-block:: bash

    check-jsonschema --help

.. list-table:: Basic Options
   :widths: 15 30
   :header-rows: 1

   * - Option
     - Description
   * - ``--schemafile``
     - The path or URL for a file containing a schema to use.
   * - ``-v``, ``--verbose``
     - Request more output.
   * - ``-q``, ``--quiet``
     - Request less output.
   * - ``-o [TEXT|JSON]``, ``--output-format [TEXT|JSON]``
     - Use this option to choose how the output is presented. Either as ``TEXT`` (the
       default) or ``JSON``, as in ``-o JSON``.
   * - ``--color [always|never|auto]``
     - Control colorization of output. ``auto`` (the default) autodetects if
       the output is a terminal. ``always`` and ``never`` enable and disable
       colorization.
   * - ``--traceback-mode [short|full]``
     - By default, when an error is encountered, ``check-jsonschema`` will pretty-print
       the error and exit. Use ``--traceback-mode full`` to request the full traceback
       be printed, for debugging and troubleshooting.

Other Schema Options
--------------------

No matter what usage form is used, a schema must be specified.

There are several options for specifying schemas in different ways, in addition
to ``--schemafile``, but at least one of them must be used.

These options are mutually exclusive, so exactly one must be used.

.. list-table:: Schema Options
   :widths: 15 30
   :header-rows: 1

   * - Option
     - Description
   * - ``--schemafile``
     - The path or URL for a file containing a schema to use.
   * - ``--builtin-schema``
     - The name of a builtin schema from ``check-jsonschema`` to use.
   * - ``--check-metaschema``
     - Validate each instancefile as a JSON Schema, using the relevant metaschema
       defined in ``"$schema"``.

``--builtin-schema`` Choices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following values are valid and refer to vendored copies schemas from
SchemaStore and other sources:

.. vendored-schema-list-start

- ``vendor.azure-pipelines``
- ``vendor.bamboo-spec``
- ``vendor.buildkite``
- ``vendor.dependabot``
- ``vendor.github-actions``
- ``vendor.github-workflows``
- ``vendor.gitlab-ci``
- ``vendor.readthedocs``
- ``vendor.renovate``
- ``vendor.travis``

.. vendored-schema-list-end

The following values refer to custom schemas:

- ``github-workflows-require-timeout`` -- This schema checks that a GitHub
  workflow explicitly sets ``timeout-minutes`` on all jobs. (The default value
  for this is 6 hours.)

Downloading and Caching
-----------------------

By default, when ``--schemafile`` is used to refer to an ``http://`` or
``https://`` location, the schema is downloaded and cached based on the
schema's Last-Modified time.
The following options control caching behaviors.

.. list-table:: Caching Options
   :widths: 15 30
   :header-rows: 1

   * - Option
     - Description
   * - ``--no-cache``
     - Disable caching.
   * - ``--cache-filename``
     - The name to use for caching a remote schema.
       Defaults to using the last slash-delimited part of the URI.

Environment Variables
---------------------

The following environment variables are supported.

.. list-table:: Environment Variables
   :widths: 15 30
   :header-rows: 1

   * - Name
     - Description
   * - ``NO_COLOR``
     - Set ``NO_COLOR=1`` to explicitly turn off colorized output.

Parsing Options
---------------

``--default-filetype``
~~~~~~~~~~~~~~~~~~~~~~

The default filetype to assume on instance files when they are detected neither
as JSON nor as YAML.

For example, pass ``--default-filetype yaml`` to instruct that files which have
no extension should be treated as YAML.

By default, this is not set and files without a detected type of JSON or YAML
will fail.

``--data-transform``
~~~~~~~~~~~~~~~~~~~~

``--data-transform`` applies a transformation to instancefiles before they are
checked. The following transforms are supported:

- ``azure-pipelines``:
    "Unpack" compile-time expressions for Azure Pipelines files, skipping them
    for the purposes of validation. This transformation is based on Microsoft's
    lanaguage-server for VSCode and how it handles expressions

- ``gitlab-ci``:
    Handle ``!reference`` tags in YAML data for gitlab-ci files. This transform
    has no effect if the data is not being loaded from YAML, and it does not
    interpret ``!reference`` usages -- it only expands them to lists of strings
    to pass schema validation

``--fill-defaults``
-------------------

JSON Schema specifies the ``"default"`` keyword as potentially meaningful for
consumers of schemas, but not for validators. Therefore, the default behavior
for ``check-jsonschema`` is to ignore ``"default"``.

``--fill-defaults`` changes this behavior, filling in ``"default"`` values
whenever they are encountered prior to validation.

.. warning::

    There are many schemas which make the meaning of ``"default"`` unclear.
    In particular, the behavior of ``check-jsonschema`` is undefined when multiple
    defaults are specified via ``anyOf``, ``oneOf``, or other forms of polymorphism.

"format" Validation Options
---------------------------

JSON Schema defines a ``"format"`` attribute for string fields but does not require
that any validation for formats be applied.

``check-jsonschema`` supports checking several ``"format"``\s by default. The
following options can be used to control this behavior.

``--disable-format``
~~~~~~~~~~~~~~~~~~~~

.. warning::

    This option is deprecated. Use ``--disable-formats "*"`` instead.

Disable all format checks.

``--disable-formats``
~~~~~~~~~~~~~~~~~~~~~

Disable specified ``"format"`` checks.

Use ``--disable-formats "*"`` to disable all format checking.

Because ``"format"`` checking is not done by all JSON Schema tools, it is
possible that a file may validate under a schema with a different tool, but
fail with ``check-jsonschema`` if ``--disable-formats`` is not set.

This option may be specified multiple times or as a comma-delimited list and
supports the following formats as arguments:

- ``date``
- ``date-time``
- ``duration``
- ``email``
- ``hostname``
- ``idn-email``
- ``idn-hostname``
- ``ipv4``
- ``ipv6``
- ``iri``
- ``iri-reference``
- ``json-pointer``
- ``regex``
- ``relative-json-pointer``
- ``time``
- ``uri``
- ``uri-reference``
- ``uri-template``
- ``uuid``

Example usage:

.. code-block:: bash

    # disables all three of time, date-time, and iri
    --disable-formats time,date-time --disable-formats iri

``--format-regex``
~~~~~~~~~~~~~~~~~~

Set a mode for handling of the ``"regex"`` value for ``"format"``. The modes are as
follows:

.. list-table:: Regex Options
   :widths: 15 30
   :header-rows: 1

   * - mode
     - description
   * - disabled
     - Skip checking ``regex``, but leave other formats enabled.
   * - default
     - Check for known non-python regex syntaxes. If one is found, the expression
       always passes. Otherwise, check validity in the python engine.
   * - python
     - Require the regex to be valid in python regex syntax.
