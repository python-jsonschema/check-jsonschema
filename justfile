set lazy
version := `uvx mddj read version`
push_remote := `git rev-parse --abbrev-ref @{push} | cut -d '/' -f1`

# show helptext
help:
    @just --list
    @echo '\nVarables:'
    @just --evaluate

# build docs and serve them locally
serve-docs:
    uvx --with 'tox-uv' tox r -e docs
    python -m http.server 8000 -d docs/_build/dirhtml/

# run all forms of linting and fixing
lint:
    pre-commit run -a
    tox run -e mypy

# run all tests
test:
    tox p

# update the vendored schema files
vendor-schemas:
    tox run -e vendor-schemas

# (re)generate the pre-commit config
generate-hooks:
    tox run -e generate-hooks-config

# bump the project version number
bump-version NEW_VERSION:
    scripts/bump-version.py "{{NEW_VERSION}}"

# tag the current commit as a release
tag-release:
    git tag -s "{{version}}" -m "v{{version}}"
    git push {{push_remote}} refs/tags/{{version}}

# collate test reports to check aggregated details
collated-test-report: test
    python ./scripts/aggregate-pytest-reports.py .tox/*/pytest.xml

# delete ephemeral files
clean:
    rm -rf dist build *.egg-info .tox .coverage.*
    find . -type d -name '__pycache__' -exec rm -r {} +
