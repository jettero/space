# coding: utf-8
# pylint: disable=redefined-outer-name

import os
import subprocess

import pytest

from space.util import same_program


@pytest.fixture
def sleeper():
    p = subprocess.Popen(["sleep", "30"])
    yield p.pid
    p.kill()
    p.wait()


@pytest.fixture
def dead_pid():
    p = subprocess.Popen(["true"])
    p.wait()
    return p.pid


def test_same_program_self():
    assert same_program(os.getpid())


def test_same_program_other_program(sleeper):
    assert not same_program(sleeper)


def test_same_program_gone(dead_pid):
    assert not same_program(dead_pid)
