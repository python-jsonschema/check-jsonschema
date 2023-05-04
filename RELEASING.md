# Releasing

- Bump the version with `./scripts/bump-version.py NEW_VERSION`
- Add, commit with `git commit -m 'Bump version for release'`, and push
- Create a release tag, which will auto-publish to testpypi (`make release`)
- Create a GitHub release, which will auto-publish to pypi (web UI)
