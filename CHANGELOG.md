# CHANGELOG

## Unreleased

<!-- vendor-insert-here -->
- Update vendored schemas (2022-06-27)

## 0.16.1

- Update vendored schemas: github-workflows, gitlab-ci, renovate (2022-06-21)
- Fix the behavior of unquoted datetime strings in YAML documents to always
  parse as strings, not `datetime.datetime`. Thanks to
  [@tgillbe](https://github.com/tgillbe) for the fix!
  ([#116](https://github.com/python-jsonschema/check-jsonschema/issues/116))

## 0.16.0

- Update vendored schemas: gitlab-ci, renovate (2022-06-06)
- Add support for TOML instance files using `tomli`. See documentation on
  optional parsers for details.
  Thanks to [@mondeja](https://github.com/mondeja) for the request and test
  data!
- Instance files are now read in binary mode, not UTF-8 encoded
- The behavior of format checkers is now more draft-specific, as
  `check-jsonschema` will now use the appropriate checker for the schema's
  dialect as detected via the `$schema` attribute

## 0.15.1

- Update vendored schemas: bamboo-spec, dependabot, github-actions,
  github-workflows, gitlab-ci, readthedocs, renovate, travis (2022-05-26)
- Add `check-dependabot` to supported hooks

## 0.15.0

- Update vendored schemas: renovate, gitlab, github-workflow, github-actions,
  azure-pipelines, readthedocs (2022-05-13)
- Use `click` to implement CLI parsing. This provides several internal features
  as well as shell completion support.
- Add support for `--version` as an option
- Add support for the `NO_COLOR=1`
- When loading schema references, check for a suffix of `.ya?ml` and emit a
  warning. This does not abort loading the reference.
- When loading YAML instance files, non-string object keys will be stringified.
  This makes YAML data better conform to the requirements for JSON Schema.
- Change usage of stderr/stdout to send more of the error information to stdout
  and more of the user-messaging to stderr
- Deprecate `--show-all-validation-errors`. It will be removed in a future
  release.
- Add `-v/--verbose` and `-o/--output-format` to offer better control over
  output. `--verbose` replaces `--show-all-validation-errors` and `-o` can be
  used to request JSON output as in `-o JSON`.

## 0.14.3

- Update vendored schemas: renovate, gitlab-ci (2022-04-13)
- `check-jsonschema` now treats all instance files as UTF-8, regardless of the
  platform and locale. This ensures that files are handled uniformly between
  \*nix and Windows

## 0.14.2

- Update vendored schemas: renovate, github-workflows, gitlab-ci (2022-03-30)
- Fix the vendored schema for GitLab to pull from the correct location.
  Thanks [@dsch](https://github.com/dsch) for the fix!

## 0.14.1

- Update vendored schemas: azure-pipelines, renovate (2022-03-17)
- Allow invocation via `python -m check_jsonschema`

## 0.14.0

- Drop support for python3.6 and improve internal type annotations
- Update vendored schemas (2022-02-28)
- Improve handling of file-URI inputs on Windows
- Add support for a new hook, `check-metaschema`, which invokes
    `check-jsonschema --check-metaschema`
- The `check-jsonschema` repo has moved to a new home at
    https://github.com/python-jsonschema/check-jsonschema

## 0.13.0

- Add support for `--check-metaschema`, which validates each instance file as a
    JSON Schema, using the metaschema specified by `"$schema"`
- `--builtin-schema` now validates its arguments (with `choices=...`), and its
    options are automatically picked up from the internal schema catalog and
    listed in the `--help` output

## 0.12.0

- Add support for JSON5 files when `pyjson5` or `json5` is installed, and
    update the Renovate hook to list JSON5 config files. If a JSON5 file is
    checked without one of the necessary packages installed, a special error
    with installation instructions will be raised
- Add hooks for GitLab CI and Bamboo Specs
- Remove the `--failover-builtin-schema` behavior. Now that vendored schemas
  are used by default for hooks, this option had very limited utility.
- Update vendored schemas (2022-02-16)

## 0.11.0

- Add support for `--data-transform azure-pipelines` to handle compile-time
  expressions in Pipelines files. This option is applied to the azure
  pipelines hook ([#29](https://github.com/python-jsonschema/check-jsonschema/issues/29))
- Improve handing of validation errors from schemas with `anyOf` and `oneOf`
  clauses. Show the "best match" from underlying errors, and add an option
  `--show-all-validation-errors` which displays all of the underlying errors
- Use vendored schemas in all hooks, not latest schemastore copies. This
  ensures that hook behavior is consistent
  ([#38](https://github.com/python-jsonschema/check-jsonschema/issues/38))
- Update vendored schemas (2022-02-12)
- Use `requests` to make HTTP requests, and retry request failures

## 0.10.2

- Fix the `check-renovate` hook, which was skipping all files. Do not attempt
  to check JSON5 files, which are not supported.
  Thanks to [@tpansino](https://github.com/tpansino) for the contribution!
- Update vendored schema versions (2022-02-01)

## 0.10.1

- Use pypa's `build` tool to build dists
- Update vendored schema versions (2022-01-27)

## 0.10.0

- Support YAML as a format for schema files (local schemas only).
  Thanks to [@yyuu](https://github.com/yyuu) for the contribution!

## 0.9.1

- Update Azure Pipelines and ReadTheDocs hooks to always download latest
  schemas (rather than specific versions). This is safe now that they can
  failover to builtin schemas
- Update Azure Pipelines schema to latest

## 0.9.0

- Format checking now has special handling for the `regex` format. The default
  looks for recognizable syntaxes which indicate the use of an engine-specific
  regex feature which cannot be parsed in python. Such regexes are always
  treated as valid. To get strict python behavior (the previous behavior), use
  `--format-regex=python`. For no regex checking at all, without disabling
  other formats, use `--format-regex=disabled`.
  resolves [#20](https://github.com/python-jsonschema/check-jsonschema/issues/20)
- Add a hook for Renovate Bot config, `check-renovate`. Note that the hook does
  not support config in `package.json` (all other configuration locations are
  supported)

## 0.8.2

- Add ReadTheDocs hook

## 0.8.1

- Bugfix for package metadata to include builtin schemas

## 0.8.0

- `check-jsonschema` now ships with vendored versions of the external schemas
  used for the default suite of hooks. The vendored schemas are used as a
  failover option in the event that downloading an external schema fails. This
  resolves [#21](https://github.com/python-jsonschema/check-jsonschema/issues/21)
- New CLI options, `--builtin-schema` and `--failover-builtin-schema` are
  available to access the builtin schemas. See documentation for details.
- Use the latest version (version 4) of the `jsonschema` library. Note
  that `jsonschema` has dropped support for python3.6, and  `check-jsonschema`
  will therefore use `jsonschema` version 3 when running on python3.6
- The path shown in error messages is now a valid
  [JSONPath](https://goessner.net/articles/JsonPath/) expression

## 0.7.1

- Bugfix: validation errors were not being displayed correctly.
- Errors are now sent to stderr instead of stdout.

## 0.7.0

- Exception tracebacks for several known-cases are printed in a shortened
  format. A new option, `--traceback-mode` can be used to request long traces,
  as in `--traceback-mode full`
- For schemas which do not include `$id`, the schema URI will be used for
  `$ref` resolution. This applies to HTTP(S) schema URI as well as to local
  paths. Thanks to [@dkolepp](https://github.com/dkolepp) for the bug report
  and contributions!

## 0.6.0

- Add support for string format verification, by enabling use of the
  `jsonschema.FormatChecker`. This is enabled by default, but can be disabled
  with the `--disable-format` flag

## 0.5.1

- Improved error output when the schema itself is invalid, either because it is
  not JSON or because it does not validate under its relevant metaschema

## 0.5.0

- Added the `--default-filetype` flag, which sets a default of JSON or YAML
  loading to use when `identify` does not detect the filetype of an instance
  file. Defaults to failure on extensionless files.
- Schemafiles are now passed through `os.path.expanduser`, meaning that a
  schema path of `~/myschema.json` will be expanded by check-jsonschema
  itself ([#9](https://github.com/python-jsonschema/check-jsonschema/issues/9))
- Performance enhancement for testing many files: only load the schema once
- Added `--no-cache` option to disable schema caching
- Change the default schema download cache directory from
  `jsonschema_validate` to `check_jsonschema/downloads`.
  e.g. `~/.cache/jsonschema_validate` is now
  `~/.cache/check_jsonschema/downloads`.
  Caches will now be in the following locations for different platforms
  and environments:

  - `$XDG_CACHE_HOME/check_jsonschema/downloads` (Linux/other, XDG cache dir)
  - `~/.cache/check_jsonschema/downloads` (Linux/other, no XDG cache dir set)
  - `~/Library/Caches/check_jsonschema/downloads` (macOS)
  - `%LOCALAPPDATA%\check_jsonschema\downloads` (Windows, local app data set)
  - `%APPDATA%\check_jsonschema\downloads` (Windows, no local app data set, but appdata set)

## 0.4.1

- Update the azure-pipelines schema version to latest.
  Thanks to [@Borda](https://github.com/Borda)

## 0.4.0

- Fix a bug with parallel runs writing the same file in an unsafe way
- Update the base cache directory on macOS to `~/Library/Caches/`.
  Thanks to [@foolioo](https://github.com/foolioo)

## 0.3.2

- Bugfix: handle last-modified header being un-set on schema request. Thanks to
  [@foolioo](https://github.com/foolioo) for the fix!

## 0.3.1

- Bugfix: handle non-string elements in the json path. Thanks to
  [@Jean-MichelBenoit](https://github.com/Jean-MichelBenoit) for the fix!

## 0.3.0

- Don't show full schemas on errors. Show only the filename, path, and message
- Convert from package to single module layout

## 0.2.1

- Add hooks for additional CI systems: Azure pipelines, GitHub Actions, and Travis

## 0.2.0

- Add `check-github-workflows` hook

## 0.1.1

- Set min pre-commit version

## 0.1.0

- Initial version
