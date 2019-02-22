
A_PY := $(shell find . -type f -name \*.py)
T_PY := $(wildcard t/*.py)

default: test

test: .setup-test
build dist: .setup-bdist
	@ ls -haltr dist/space-*.tar.gz
help:
	python setup.py --help-commands

.setup-test: $(A_PY)
.setup-build: .setup-test
.setup-bdist: .setup-test

.setup-%:
	python setup.py $*
	@touch $@

clean:
	git clean -dfx
