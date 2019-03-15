
A_PY := $(shell find . -type f -name \*.py)
T_PY := $(wildcard t/test_*.py)

default: test

venv:
	virtualenv venv

venv-test: venv
	+ rm -vf .setup-test; . venv/bin/activate && make --no-print-directory test

test: .setup-test
build dist: .setup-bdist
	@ ls -haltr dist/space-*.tar.gz
help:
	python setup.py --help-commands

# requirements.txt: setup.py
#     pip install -U pip pip-tools
#     pip-compile -o $@ $<

# .pip-install: requirements.txt
#     @ [ -f $@ ] && rm -v $@; true
#     pip install --upgrade -r $< && touch $@

.setup-test: $(A_PY) # .pip-install
.setup-build: .setup-test
.setup-bdist: .setup-test

.setup-%:
	python setup.py $*
	@touch $@

clean:
	git clean -dfx
