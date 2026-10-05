
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

APPSERV := contrib/appserv
APPSERV_BIN := $(APPSERV)/target/debug/appserv
APPSERV_PREFIX := $(CURDIR)/$(APPSERV)/data

appserv:
	$(MAKE) -C $(APPSERV) target/debug/appserv

$(APPSERV_PREFIX)/.space-deps: requirements.txt | appserv
	$(APPSERV_BIN) --prefix $(APPSERV_PREFIX) --pip "install -r $(CURDIR)/requirements.txt"
	@ date > $@

start: appserv $(APPSERV_PREFIX)/.space-deps
	$(APPSERV_BIN) --prefix $(APPSERV_PREFIX) --entry as_entry.py --prepend-path $(CURDIR) --bind 127.0.0.1:2222 $(if $(MAP),--py-arg $(CURDIR)/$(MAP))

.PHONY: appserv start

%.png: %.dot
	dot -Tpng $< -o $@

show-parser-graph: parser.png
	DISPLAY=:0.0 xdg-open parser.png &>/dev/null
