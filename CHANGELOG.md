# CHANGELOG

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
