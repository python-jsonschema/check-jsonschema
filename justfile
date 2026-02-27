version := `uvx mddj read version`
push_remote := `git rev-parse --abbrev-ref @{push} | cut -d '/' -f1`

lint:
    pre-commit run -a
    tox run -e mypy

test:
    tox p

vendor-schemas:
    tox run -e vendor-schemas

generate-hooks:
    tox run -e generate-hooks-config

tag-release:
    git tag -s "{{version}}" -m "v{{version}}"
    git push {{push_remote}} refs/tags/{{version}}

collated-test-report: test
    python ./scripts/aggregate-pytest-reports.py .tox/*/pytest.xml

clean:
    rm -rf dist build *.egg-info .tox .coverage.*
    find . -type d -name '__pycache__' -exec rm -r {} +
