# CHANGELOG

## Unreleased

## 0.8.1

- Bugfix for package metadata to include builtin schemas

## 0.8.0

- `check-jsonschema` now ships with vendored versions of the external schemas
  used for the default suite of hooks. The vendored schemas are used as a
  failover option in the event that downloading an external schema fails. This
  resolves [#21](https://github.com/sirosen/check-jsonschema/issues/21))
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
  itself ([#9](https://github.com/sirosen/check-jsonschema/issues/9))
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
