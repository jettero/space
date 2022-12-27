

test:
	pytest t

clean:
	git clean -dfx

reqs mods: test-requirements.txt requirements.txt
	pip install -U pip wheel
	pip install -Ur test-requirements.txt
	@ date > reqs; date > mods
