PKG_VERSION=$(shell grep '^version' setup.cfg | cut -d '=' -f2 | tr -d ' ')

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
	tox run -e publish-release

.PHONY: collated-test-report
collated-test-report:
	tox p -e py37-mindeps,py311,py310-notoml,py310-tomli-format,py311-json5  -- '--junitxml={envdir}/pytest.xml'
	python ./scripts/aggregate-pytest-reports.py \
		.tox/py37-mindeps/pytest.xml \
		.tox/py311/pytest.xml \
		.tox/py310-notoml/pytest.xml \
		.tox/py310-tomli-format/pytest.xml \
		.tox/py311-json5/pytest.xml

.PHONY: clean
clean:
	rm -rf dist build *.egg-info .tox .coverage.*
