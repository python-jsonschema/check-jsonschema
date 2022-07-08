Installation
============

``check-jsonschema`` is distributed as a python package.
Install with ``pip`` or ``pipx``:

.. code-block:: bash

    pip install check-jsonschema

    # or pipx
    pipx install check-jsonschema


Supported Pythons
-----------------

``check-jsonschema`` requires Python 3 and supports all of the versions which
are maintained by the CPython team.

It is only tested on cpython but should work on other interpreters as well.

Do not use ``pip install --user``
---------------------------------

If installing with ``pip``, make sure you use a virtualenv to isolate the
installation from the rest of your system.

``pip install --user check-jsonschema`` might work and seem convenient, but it
has problems which ``pipx`` or virtualenv usage resolve.


No install for pre-commit
-------------------------

If you are using ``pre-commit`` to run ``check-jsonschema``, no installation is
necessary. ``pre-commit`` will automatically install and run the hooks.
