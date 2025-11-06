# coding: utf-8


def test_shell_basic(shell_proc):
    shell_proc.sendline("look")
    ok, _ = shell_proc.expect(r"/space/ ", timeout=1)
    assert ok


def test_shell_no_double_prompt(shell_proc):
    shell_proc.expect(r"/space/ ", timeout=2)
    ok, data = shell_proc.expect("Application is already running.", timeout=10)
    assert not ok, data
    assert "Application is already running." not in shell_proc.captured
