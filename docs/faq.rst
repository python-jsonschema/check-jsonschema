FAQ
===

How do I use check-jsonschema in my application?
------------------------------------------------

``check-jsonschema`` is only a CLI application, not a library for import and
use within python applications.

It is powered by the
`jsonschema <https://python-jsonschema.readthedocs.io/en/stable/>`_ library.
Most users looking to integrate JSON Schema in their applications should look
into using ``jsonschema`` directly.

It is also safe and supported to run ``check-jsonschema`` in a process, invoking
it with correct CLI arguments and checking the output.

Python Subprocess Invocation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following snippet for python applications ensures that you are running with
the current interpreter and runs the equivalent of
``check-jsonschema --version``:

.. code-block:: python

    import subprocess
    import sys

    result = subprocess.check_output([sys.executable, "-m", "check_jsonschema", "--version"])
    print(result.decode())

Non-Python Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~

When invoking ``check-jsonschema`` from another language in a process, make
sure you control the installation of ``check-jsonschema``. For example, the
following Ruby snippet may look safe:

.. code-block:: ruby

    require 'json'

    raw_data = `check-jsonschema -o JSON --schemafile #{schema} #{instance}`
    data = JSON.parse(raw_data)

However, it could be problematic if run in environments with different
versions of ``check-jsonschema`` installed.

One way to handle this is to install ``check-jsonschema`` into a virtualenv and
always invoke it explicitly from that virtualenv, as in

.. code-block:: ruby

    require 'json'

    raw_data = `venv/bin/check-jsonschema -o JSON --schemafile #{schema} #{instance}`
    data = JSON.parse(raw_data)

GitHub Actions Workflows
------------------------

Using Self-Hosted Runners
~~~~~~~~~~~~~~~~~~~~~~~~~

The GitHub Actions Workflow schema defined in SchemaStore does not allow all
valid workflows, but rather a specific subset of workflows.

For self-hosted runners, the schema will reject ``runs-on`` with an unrecognized
string value. In order to use a custom runner ``runs-on`` value, put it into an
array with ``self-hosted``, like so:

.. code-block:: yaml

    name: self-hosted job
    on:
      push:

    jobs:
      myjob:
        runs-on: [self-hosted, spot-self-hosted]
        steps:
          - run: echo 'hi'
