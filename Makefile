PKG_VERSION=$(shell grep '^version' setup.cfg | cut -d '=' -f2 | tr -d ' ')

.PHONY: lint test vendor-schemas generate-hooks release showvars
lint:
	pre-commit run -a
test:
	tox
vendor-schemas:
	tox -e vendor-schemas
generate-hooks:
	tox -e generate-hooks-config
showvars:
	@echo "PKG_VERSION=$(PKG_VERSION)"
release:
	git tag -s "$(PKG_VERSION)" -m "v$(PKG_VERSION)"
	-git push $(shell git rev-parse --abbrev-ref @{push} | cut -d '/' -f1) refs/tags/$(PKG_VERSION)
	tox -e publish-release

.PHONY: clean
clean:
	rm -rf dist build *.egg-info .tox
