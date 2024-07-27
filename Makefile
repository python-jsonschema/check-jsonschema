PKG_VERSION=$(shell grep '^version' pyproject.toml | head -n1 | cut -d '"' -f2)

.PHONY: lint test vendor-schemas generate-hooks release showvars
lint:
	pre-commit run -a
	tox run -e mypy
test:
	tox run
vendor-schemas:
	tox run -e vendor-schemas
generate-hooks:
	tox run -e generate-hooks-config
showvars:
	@echo "PKG_VERSION=$(PKG_VERSION)"
release:
	git tag -s "$(PKG_VERSION)" -m "v$(PKG_VERSION)"
	-git push $(shell git rev-parse --abbrev-ref @{push} | cut -d '/' -f1) refs/tags/$(PKG_VERSION)

.PHONY: collated-test-report
collated-test-report:
	tox p
	python ./scripts/aggregate-pytest-reports.py .tox/*/pytest.xml

.PHONY: clean
clean:
	rm -rf dist build *.egg-info .tox .coverage.*
