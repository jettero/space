#!/usr/bin/env python
# coding: utf-8

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)

mods = ['lark-parser', 'pint']

setup(name='space',
    use_scm_version = {
        'write_to': 'space/version.py',
        'tag_regex': r'^(?P<prefix>v)(?P<version>\d+\.\d+\.\d+)(?P<suffix>.*)?$',
        # NOTE: use ./setup.py --version to regenerate version.py and print the
        # computed version
    },
    description      = '/space/ — game engine',
    author           = 'Paul Miller',
    author_email     = 'paul@jettero.pl',
    url              = 'https://github.com/jettero/space/',
    tests_require    = ['pytest',] + mods,
    cmdclass         = {'test': PyTest},
    packages         = find_packages(),
    setup_requires   = [ 'setuptools_scm' ],
    install_requires = mods,
)
