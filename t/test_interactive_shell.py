# coding: utf-8


def test_shell_basic(shell_proc):
    shell_proc.sendline("look")
    ok, _ = shell_proc.expect(r"/space/ ", timeout=1)
    assert ok
