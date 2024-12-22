.. Unlike other docs, the changelog is incorporated into a sphinx doc site in
.. which we want to use sphinx-issues to generate links.
.. As a result, it's maintained as ReST doc, not markdown.

CHANGELOG
=========

Unreleased
----------

.. vendor-insert-here

- Update vendored schemas (2024-12-22)

0.30.0
------

- Update vendored schemas: azure-pipelines, bitbucket-pipelines, buildkite,
  circle-ci, cloudbuild, dependabot, github-workflows, gitlab-ci, mergify,
  readthedocs, renovate, taskfile, woodpecker-ci (2024-11-29)
- Fix caching behavior to always use URL hashes as cache keys. This fixes a
  cache confusion bug in which the wrong schema could be retrieved from the
  cache. This resolves :cve:`2024-53848`. Thanks :user:`sethmlarson` for reporting!
- Deprecate the ``--cache-filename`` flag. It no longer has any effect and will
  be removed in a future release.

0.29.4
------

- Update vendored schemas: azure-pipelines, github-workflows, gitlab-ci,
  mergify, renovate (2024-10-06)
- Fix the renovate hook to allow for ``.renovaterc.json5`` as well. Thanks
  :user:`tpansino`! (:pr:`491`)
- Add Mergify schema and pre-commit hook. Thanks :user:`hofbi` and :user:`jd`
  for the issue and feedback! (:issue:`487`)

0.29.3
------

- Update vendored schemas: buildkite, circle-ci, dependabot, gitlab-ci,
  renovate, taskfile, woodpecker-ci (2024-09-29)

0.29.2
------

- Update vendored schemas: buildkite, github-workflows, gitlab-ci, renovate,
  woodpecker-ci  (2024-08-22)
- Convert from ``setup.cfg`` to ``pyproject.toml`` for python package metadata

0.29.1
------

- Update vendored schemas: circle-ci, dependabot, gitlab-ci, renovate,
  woodpecker-ci (2024-07-21)
- Fix a bug which could result in local file URI resolution failing on
  non-Windows platforms in certain cases. Thanks :user:`bukzor`! (:pr:`465`)
- Fix caching behaviors to ensure that caches are correctly preserved across
  instancefiles during ``--schemafile`` evaluation. This also fixes a bug in the
  remote ``$ref`` cache.
  Thanks :user:`alex1701c` for reporting! (:issue:`463`, :pr:`466`)

0.29.0
------

- Update vendored schemas: github-workflows, renovate, woodpecker-ci (2024-07-07)
- Improve caching to include caching of remote ``$ref`` downloads. This should
  improve performance in cases where a schema has many remote refs and is used
  in repeat invocations. The ``$ref`` cache can be disabled via the same
  ``--no-cache`` flag which disables use of the pre-existing cache. Thanks
  :user:`alex1701c`! (:issue:`452`, :pr:`454`)
- Fix an ordering bug which caused caching to be ineffective, resulting in
  repeated downloads of remote schemas even when the cache was populated.
  Thanks :user:`alex1701c` for reporting! (:issue:`453`)

0.28.6
------

- Update vendored schemas: bitbucket-pipelines, circle-ci, readthedocs,
  renovate (2024-06-23)
- Add CircleCI schema and pre-commit hook. Thanks :user:`jrdnbradford`! (:pr:`444`)

0.28.5
------

- Update vendored schemas: bitbucket-pipelines, dependabot, github-actions,
  github-workflows, gitlab-ci, readthedocs, renovate (2024-06-10)
- Update bitbucket schema to use the option from the
  intellij-bitbucket-references-plugin . For more details on this decision, see
  :issue:`440` . Thanks @blade2005 for the PR! (:pr:`442`)

0.28.4
------

- Update vendored schemas: buildkite, github-workflows, gitlab-ci, renovate,
  taskfile, woodpecker-ci (2024-05-19)

0.28.3
------

- Update vendored schemas: dependabot, github-workflows, gitlab-ci, renovate,
  woodpecker-ci (2024-05-05)
- Update Cloud Build pre-commit hook to support JSON Cloud Build config. Thanks
  :user:`jrdnbradford`! (:pr:`427`)

0.28.2
------

- Update vendored schemas: cloudbuild, gitlab-ci, renovate (2024-04-10)
- Add Taskfile schema and pre-commit hook. Thanks :user:`jrdnbradford`! (:pr:`417`)

0.28.1
------

- Update vendored schemas: buildkite, cloudbuild, dependabot, github-actions,
  github-workflows, gitlab-ci, renovate, woodpecker-ci (2024-03-31)

0.28.0
------

- Update vendored schemas: cloudbuild, dependabot, gitlab-ci, readthedocs,
  renovate (2024-02-06)
- Include built-in, efficient implementations of ``date-time`` format validation
  (RFC 3339) and ``time`` format validation (ISO 8601). This makes the ``date-time``
  and ``time`` formats always available for validation. (:issue:`378`)
- Support the use of ``orjson`` for faster JSON parsing when it is installed.
  This makes it an optional parser which is preferred over the default
  ``json`` module when it is available.
- TOML parsing is now always available (rather than an optional parser).
  This change adds a dependency on ``tomli`` on older Python versions, ensuring
  that TOML formatted data is always supported. Users should no longer need
  to install ``tomli`` manually in order to use TOML files.

0.27.4
------

- Update vendored schemas: cloudbuild, dependabot, drone-ci, github-actions,
  github-workflows, gitlab-ci, renovate, travis (2024-01-29)
- Add Woodpecker-CI schema and pre-commit hook. Thanks :user:`6543`! (:pr:`380`)

0.27.3
------
- Update vendored schemas: bitbucket, gitlab-ci, readthedocs, renovate
  (2023-12-05)
- Limit the number of instance files which are opened simultaneously, which
  avoids reaching OS limits for open file descriptors. Thanks
  :user:`ianmackinnon`! (:issue:`352`)
- Improve handling of schemafiles to ensure that they are only read once
  (:pr:`363`)

0.27.2
------

- Update vendored schemas: dependabot, github-workflows, renovate (2023-11-24)
- Add official support for Python 3.12
- Add Google Cloud Build schema and pre-commit hook. Thanks :user:`nikolaik`!
  (:pr:`339`)
- Fix a bug in the custom ``github-workflows-require-timeout`` schema which forbade
  the use of GitHub expression syntax for the timeout value. (:issue:`354`)

0.27.1
------

- Update vendored schemas: buildkite, drone-ci, github-workflows, gitlab-ci,
  readthedocs, renovate (2023-11-03)

0.27.0
------

- Update vendored schemas: azure-pipelines, bitbucket-pipelines, gitlab-ci,
  renovate (2023-09-27)
- Add a ``--validator-class`` option for specifying a custom
  ``jsonschema.protocols.Validator`` class to use (:pr:`327`, :issue:`262`)
- Instances and schemas may now be passed on stdin, using ``-`` (:pr:`332`,
  :issue:`251`)
- Minor fix to hook regexes to explicitly match ``.`` chars. Thanks
  :user:`skwde`! (:pr:`325`)

0.26.3
------

- Fix a minor bug with the verbose output introduced in v0.26.2

0.26.2
------

- When ``-v/--verbose`` is used, output will include a list of all files which
  were checked on success (:issue:`312`)

0.26.1
------

- Update vendored schemas: github-workflows, renovate (2023-08-25)

0.26.0
------
- The regex format check has been improved to support ECMAScript regexes by
  default. (:issue:`302`)
- The ``--format-regex disabled`` option has been removed. Users should use
  ``--disable-formats regex`` if they wish to disable regex format checking.
- The deprecated ``--disable-format`` flag has been removed. Users should use
  ``--disable-formats "*"`` if they wish to disable all format checking.

0.25.0
------

- Update vendored schemas: bamboo-spec, dependabot, drone-ci, github-actions,
  github-workflows, readthedocs, renovate, travis (2023-08-25)
- Add Drone-CI schema and pre-commit hook. Thanks :user:`s-weigand`!
  (:pr:`299`)
- Add a ``--base-uri`` option for specifying an explicit base URI (:pr:`305`)

0.24.1
------

- Fix bugs related to the new `$ref` resolution behavior

0.24.0
------

- Update vendored schemas: github-actions, gitlab-ci, readthedocs, renovate,
  travis (2023-08-08)
- Remove support for python3.7
- The minimum supported version of the ``jsonschema`` library is now ``4.18.0``,
  which introduces new ``$ref`` resolution behavior and fixes. That behavior is
  used in all cases, which should result in faster evaluation especially on
  large schemas.
- ``$ref`` usage may now refer to YAML, TOML, or JSON5 files, or any other
  non-JSON format supported by ``check-jsonschema``. The file type is inferred
  only from the file extension in these cases and defaults to JSON if there is
  no recognizable extension.
- Remote schemafiles (http/s) now support YAML, TOML, and JSON5 formats, if the
  URL ends with the appropriate extension and the matching parser is available.
  Extensionless URLs are treated as JSON.

0.23.3
------

- Update vendored schemas: buildkite, dependabot, github-workflows, gitlab-ci,
  readthedocs, renovate (2023-07-11)
- Add Bitbucket Pipelines schema and pre-commit hook. Thanks :user:`djgoku`!
  (:pr:`282`)

0.23.2
------
- Update vendored schemas: github-workflow, gitlab-ci, renovate (2023-06-13)
- Fix the handling of malformed and missing ``Last-Modified`` headers in the
  caching downloader. Thanks :user:`balihb`! (:issue:`275`)

0.23.1
------

- Update vendored schemas: github-workflows, gitlab-ci, renovate (2023-05-30)
- The schema for enforcing timeout-minutes on GitHub Actions jobs has been
  updated to allow for workflow call jobs (which cannot have a timeout)

0.23.0
------

- Update vendored schemas: azure-pipelines, buildkite, dependabot,
  github-workflows, gitlab-ci, renovate (2023-05-03)
- A new option, ``--disable-formats`` replaces and enhances the
  ``--disable-format`` flag. ``--disable-formats`` takes a format to disable
  and may be passed multiple times, allowing users to opt out of any specific
  format checks. ``--disable-formats "*"`` can be used to disable all format
  checking. ``--disable-format`` is still supported, but is deprecated and
  emits a warning.

0.22.0
------

- Update vendored schemas: buildkite, github-workflows, gitlab-ci, renovate,
  travis (2023-03-08)
- The ``check-dependabot`` hook now also supports ``.github/dependabot.yaml``
  Thanks :user:`noorul`!
- Fix a mistake in the dependency bound for ``jsonschema``, which was intended
  to change in v0.21.0

0.21.0
------

- Update vendored schemas: github-workflows, gitlab-ci, renovate (2023-01-24)
- Fix a bug in which ``--check-metaschema`` was not building validators correctly.
  The metaschema's schema dialect is chosen correctly now, and metaschema
  formats are now checked by default. This can be disabled with
  ``--disable-format``.
- Fix the resolution of ``$schema`` dialect to format checker classes
- Fix package dependency lower bounds, including setting ``jsonschema>=4.5.1``
- Output colorization can now be controlled with
  ``--color [never|always|auto]``. Thanks :user:`WillDaSilva`!

0.20.0
------

- Update vendored schemas: bamboo-spec, buildkite, dependabot, github-actions,
  github-workflows, gitlab-ci, readthedocs, renovate, travis (2023-01-03)
- Add ``--fill-defaults`` argument which eagerly populates ``"default"``
  values whenever they are encountered and a value is not already present
  (:issue:`200`)
- Add Buildkite schema and pre-commit hook (:issue:`198`)

0.19.2
------

- Update vendored schemas: gitlab-ci, renovate (2022-11-14)
- Downloads of schemas from remote (http/https) locations will now retry if the
  downloaded data is not valid JSON (:issue:`183`)
- Remove the deprecated ``--show-all-validation-errors`` option
- Add support for Python 3.11, and ``tomllib`` as an alternative to ``tomli``
- The github-actions hook now requires a filename of ``action.yml`` or
  ``action.yaml`` for action definitions in ``.github/actions/``, in accordance
  with the GitHub Documentation (:pr:`186`)

0.19.1
------

- Fix handling of file descriptors created using the ``/proc/self/fd/``
  mechanism (:issue:`176`)

0.19.0
------

- Update vendored schemas: github-workflows, gitlab-ci, renovate (2022-11-10)
- Improve the behaviors of filetype detection. ``--default-filetype`` now
  defaults to ``json``, and can be passed ``toml`` or ``json5`` if those
  parsers are installed. Detection is now only done by suffix mapping and will
  not attempt to read files.

0.18.4
------

- Update vendored schemas: bamboo-spec, dependabot, github-workflows,
  gitlab-ci, renovate (2022-10-20)
- Tweak format checker usage to avoid deprecation warning from ``jsonschema``
- The Azure Pipelines data transform is now more permissive, which should allow
  it to handle a wider variety of pipelines files (:issue:`162`)

0.18.3
------

- Update vendored schemas: github-actions, github-workflows, renovate, travis
  (2022-09-13)

0.18.2
------

- Fix handling of certain YAML parsing errors on bad inputs

0.18.1
------

- Fix erroneous type annotations

0.18.0
------

- Update vendored schemas: azure-pipelines, github-workflows, gitlab-ci,
  renovate (2022-08-27)
- When an instancefile is invalid and cannot be parsed, validation is still run
  on all other files. The run will be marked as failed, but a more detailed
  report will be output, including validation failures on other files
  (:issue:`141`)

0.17.1
------

- Update vendored schemas: renovate (2022-07-13)
- Update check-github-worfklows match rule to exclude subdirectories of the
  ``.github/workflows/`` directory. (:issue:`113`)

0.17.0
------

- Update vendored schemas: renovate, travis (2022-06-29)
- Add support for ``--data-transform gitlab-ci``, which enables expansion of the
  ``!reference`` tag in gitlab CI YAML files. This is now enabled by default on
  the gitlab-ci pre-commit hook.
- Support for various file formats has been refactored to share code between
  the instance and schema loaders. Schema loading can now support the same
  formats as instances with minimal effort.
- Support loading schemas from JSON5 files. Like YAML schemas, this is only
  supported for local files and warns if refs to other JSON5 files are used.
- Introduce new documentation site at https://check-jsonschema.readthedocs.io

0.16.2
------

- Update vendored schemas: github-workflows, gitlab-ci, renovate (2022-06-27)
- Fix the behavior of unquoted datetime strings in YAML documents to always
  parse as strings, not ``datetime.datetime``. Thanks to :user:`tgillbe` for
  the fix! (:issue:`116`)

0.16.1
------

- Update vendored schemas: github-workflows, gitlab-ci, renovate (2022-06-21)

0.16.0
------

- Update vendored schemas: gitlab-ci, renovate (2022-06-06)
- Add support for TOML instance files using ``tomli``. See documentation on
  optional parsers for details.
  Thanks to :user:`mondeja` for the request and test
  data!
- Instance files are now read in binary mode, not UTF-8 encoded
- The behavior of format checkers is now more draft-specific, as
  ``check-jsonschema`` will now use the appropriate checker for the schema's
  dialect as detected via the ``$schema`` attribute

0.15.1
------

- Update vendored schemas: bamboo-spec, dependabot, github-actions,
  github-workflows, gitlab-ci, readthedocs, renovate, travis (2022-05-26)
- Add ``check-dependabot`` to supported hooks

0.15.0
------

- Update vendored schemas: renovate, gitlab, github-workflow, github-actions,
  azure-pipelines, readthedocs (2022-05-13)
- Use ``click`` to implement CLI parsing. This provides several internal features
  as well as shell completion support.
- Add support for ``--version`` as an option
- Add support for the ``NO_COLOR=1``
- When loading schema references, check for a suffix of ``.ya?ml`` and emit a
  warning. This does not abort loading the reference.
- When loading YAML instance files, non-string object keys will be stringified.
  This makes YAML data better conform to the requirements for JSON Schema.
- Change usage of stderr/stdout to send more of the error information to stdout
  and more of the user-messaging to stderr
- Deprecate ``--show-all-validation-errors``. It will be removed in a future
  release.
- Add ``-v/--verbose`` and ``-o/--output-format`` to offer better control over
  output. ``--verbose`` replaces ``--show-all-validation-errors`` and ``-o`` can be
  used to request JSON output as in ``-o JSON``.

0.14.3
------

- Update vendored schemas: renovate, gitlab-ci (2022-04-13)
- ``check-jsonschema`` now treats all instance files as UTF-8, regardless of the
  platform and locale. This ensures that files are handled uniformly between
  \*nix and Windows

0.14.2
------

- Update vendored schemas: renovate, github-workflows, gitlab-ci (2022-03-30)
- Fix the vendored schema for GitLab to pull from the correct location.
  Thanks :user:`dsch` for the fix!

0.14.1
------

- Update vendored schemas: azure-pipelines, renovate (2022-03-17)
- Allow invocation via ``python -m check_jsonschema``

0.14.0
------

- Drop support for python3.6 and improve internal type annotations
- Update vendored schemas (2022-02-28)
- Improve handling of file-URI inputs on Windows
- Add support for a new hook, ``check-metaschema``, which invokes
    ``check-jsonschema --check-metaschema``
- The ``check-jsonschema`` repo has moved to a new home at
    https://github.com/python-jsonschema/check-jsonschema

0.13.0
------

- Add support for ``--check-metaschema``, which validates each instance file as a
    JSON Schema, using the metaschema specified by ``"$schema"``
- ``--builtin-schema`` now validates its arguments (with ``choices=...``), and its
    options are automatically picked up from the internal schema catalog and
    listed in the ``--help`` output

0.12.0
------

- Add support for JSON5 files when ``pyjson5`` or ``json5`` is installed, and
    update the Renovate hook to list JSON5 config files. If a JSON5 file is
    checked without one of the necessary packages installed, a special error
    with installation instructions will be raised
- Add hooks for GitLab CI and Bamboo Specs
- Remove the ``--failover-builtin-schema`` behavior. Now that vendored schemas
  are used by default for hooks, this option had very limited utility.
- Update vendored schemas (2022-02-16)

0.11.0
------

- Add support for ``--data-transform azure-pipelines`` to handle compile-time
  expressions in Pipelines files. This option is applied to the azure
  pipelines hook (:issue:`29`)
- Improve handing of validation errors from schemas with ``anyOf`` and ``oneOf``
  clauses. Show the "best match" from underlying errors, and add an option
  ``--show-all-validation-errors`` which displays all of the underlying errors
- Use vendored schemas in all hooks, not latest schemastore copies. This
  ensures that hook behavior is consistent
  (:issue:`38`)
- Update vendored schemas (2022-02-12)
- Use ``requests`` to make HTTP requests, and retry request failures

0.10.2
------

- Fix the ``check-renovate`` hook, which was skipping all files. Do not attempt
  to check JSON5 files, which are not supported.
  Thanks to :user:`tpansino` for the contribution!
- Update vendored schema versions (2022-02-01)

0.10.1
------

- Use pypa's ``build`` tool to build dists
- Update vendored schema versions (2022-01-27)

0.10.0
------

- Support YAML as a format for schema files (local schemas only).
  Thanks to :user:`yyuu` for the contribution!

0.9.1
-----

- Update Azure Pipelines and ReadTheDocs hooks to always download latest
  schemas (rather than specific versions). This is safe now that they can
  failover to builtin schemas
- Update Azure Pipelines schema to latest

0.9.0
-----

- Format checking now has special handling for the ``regex`` format. The default
  looks for recognizable syntaxes which indicate the use of an engine-specific
  regex feature which cannot be parsed in python. Such regexes are always
  treated as valid. To get strict python behavior (the previous behavior), use
  ``--format-regex=python``. For no regex checking at all, without disabling
  other formats, use ``--format-regex=disabled``.
  resolves :issue:`20`
- Add a hook for Renovate Bot config, ``check-renovate``. Note that the hook does
  not support config in ``package.json`` (all other configuration locations are
  supported)

0.8.2
-----

- Add ReadTheDocs hook

0.8.1
-----

- Bugfix for package metadata to include builtin schemas

0.8.0
-----

- ``check-jsonschema`` now ships with vendored versions of the external schemas
  used for the default suite of hooks. The vendored schemas are used as a
  failover option in the event that downloading an external schema fails. This
  resolves :issue:`21`
- New CLI options, ``--builtin-schema`` and ``--failover-builtin-schema`` are
  available to access the builtin schemas. See documentation for details.
- Use the latest version (version 4) of the ``jsonschema`` library. Note
  that ``jsonschema`` has dropped support for python3.6, and  ``check-jsonschema``
  will therefore use ``jsonschema`` version 3 when running on python3.6
- The path shown in error messages is now a valid
  `JSONPath <https://goessner.net/articles/JsonPath/>`_ expression

0.7.1
-----

- Bugfix: validation errors were not being displayed correctly.
- Errors are now sent to stderr instead of stdout.

0.7.0
-----

- Exception tracebacks for several known-cases are printed in a shortened
  format. A new option, ``--traceback-mode`` can be used to request long traces,
  as in ``--traceback-mode full``
- For schemas which do not include ``$id``, the schema URI will be used for
  ``$ref`` resolution. This applies to HTTP(S) schema URI as well as to local
  paths. Thanks to :user:`dkolepp` for the bug report and contributions!

0.6.0
-----

- Add support for string format verification, by enabling use of the
  ``jsonschema.FormatChecker``. This is enabled by default, but can be disabled
  with the ``--disable-format`` flag

0.5.1
-----

- Improved error output when the schema itself is invalid, either because it is
  not JSON or because it does not validate under its relevant metaschema

0.5.0
-----

- Added the ``--default-filetype`` flag, which sets a default of JSON or YAML
  loading to use when ``identify`` does not detect the filetype of an instance
  file. Defaults to failure on extensionless files.
- Schemafiles are now passed through ``os.path.expanduser``, meaning that a
  schema path of ``~/myschema.json`` will be expanded by check-jsonschema
  itself (:issue:`9`)
- Performance enhancement for testing many files: only load the schema once
- Added ``--no-cache`` option to disable schema caching
- Change the default schema download cache directory from
  ``jsonschema_validate`` to ``check_jsonschema/downloads``.
  e.g. ``~/.cache/jsonschema_validate`` is now
  ``~/.cache/check_jsonschema/downloads``.
  Caches will now be in the following locations for different platforms
  and environments:

  - ``$XDG_CACHE_HOME/check_jsonschema/downloads`` (Linux/other, XDG cache dir)
  - ``~/.cache/check_jsonschema/downloads`` (Linux/other, no XDG cache dir set)
  - ``~/Library/Caches/check_jsonschema/downloads`` (macOS)
  - ``%LOCALAPPDATA%\check_jsonschema\downloads`` (Windows, local app data set)
  - ``%APPDATA%\check_jsonschema\downloads`` (Windows, no local app data set, but appdata set)

0.4.1
-----

- Update the azure-pipelines schema version to latest. Thanks to :user:`Borda`

0.4.0
-----

- Fix a bug with parallel runs writing the same file in an unsafe way
- Update the base cache directory on macOS to ``~/Library/Caches/``.
  Thanks to :user:`foolioo`

0.3.2
-----

- Bugfix: handle last-modified header being un-set on schema request. Thanks to
  :user:`foolioo` for the fix!

0.3.1
-----

- Bugfix: handle non-string elements in the json path. Thanks to
  :user:`Jean-MichelBenoit` for the fix!

0.3.0
-----

- Don't show full schemas on errors. Show only the filename, path, and message
- Convert from package to single module layout

0.2.1
-----

- Add hooks for additional CI systems: Azure pipelines, GitHub Actions, and Travis

0.2.0
-----

- Add ``check-github-workflows`` hook

0.1.1
-----

- Set min pre-commit version

0.1.0
-----

- Initial version
