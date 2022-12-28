
default: test

BUILD_INVENTORY := $(shell find space/ -type f -name \*.py) setup.cfg pyproject.toml

space.egg-info/PKG-INFO: $(BUILD_INVENTORY) reqs
	python -m build

build: space.egg-info/PKG-INFO

test:
	pytest t

clean:
	git clean -dfx

reqs mods: test-requirements.txt requirements.txt
	pip install -U pip wheel
	pip install -Ur test-requirements.txt
	@ date > reqs; date > mods
