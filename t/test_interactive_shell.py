# coding: utf-8

from t.shellexpect import shell_proc


def test_shell_basic(shell_proc):
    ok, _ = shell_proc.expect("/space/ ")
    assert ok
    shell_proc.sendline("look")
    ok, _ = shell_proc.expect("/space/ ")
    assert ok

