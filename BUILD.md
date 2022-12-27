# where is the setup.py?

Yeah, that hasn't been a thing since like 2021. Pfft. (I rarely remember what
you're supposed to do instead though.)

To install, you just
```
pip install .
```

And to build a binary or whatever, you'd do something like this
```
pip install build
python -m build
```

The whole point of using setup.cfg and pyproject.toml instead of setup.py is so
to allow different tools to evolve in place of setuptools (which never wanted to
be in the scripting business in the first place apparently).

There's actually a [whole matrix](https://wiki.python.org/moin/ConfigurationAndBuildTools) of build tools.
There's a similar
[matrix](https://wiki.python.org/moin/PythonTestingToolsTaxonomy) of testing
tools as well.

## pyproject.toml and setup.cfg

Wait, why do you have both? Isn't one replace to supplant the other?

IMO, `pyproject.toml` isn't done cooking yet. I like the syntax for
`setuptools_scm`, but I quickly found that if you have `setuptools_scm` generate
the `version.py` file, there's no way to also import the version from it using
only `pyproject.toml`.

Near as I can tell, they're still working on this chicken/egg problem. I think
they're reluctant to do the needful becuase the toml should be parsable in one
pass and the idea of reducing the optimality is unpalatable -- but this is just
speculation on my part.

If you know of a way to generate `version.py` from `git --describe` and import
the version into `pyproject.toml` (or otherwise express this without using `sed`
or a `Makefile`), please definitely let me know.

## Makefiles now too?

Yeah, I like makefiles. I kinda miss 'em and without that one centralized
`./setup.py <cmd>` to work with, ... seems pretty handy again all of a sudden.
