import time

from space.master import MasterControlProgram


def test_call_out_one_shot():
    mcp = MasterControlProgram()
    called = []

    def cb(x):
        called.append(x)

    mcp.call_out(cb, 0.02, 7)
    # wait a short while; allow for coarse timing
    time.sleep(0.05)
    assert called == [7]
    mcp.stop_timers()


def test_every_repeats_and_cancel():
    mcp = MasterControlProgram()
    called = []

    def tick():
        called.append(time.monotonic())

    label = "ticker"
    mcp.every(0.02, tick, label=label)
    time.sleep(0.08)
    # should have fired a few times
    assert len(called) >= 2
    # cancel and ensure it stops increasing
    mcp.cancel(label)
    n = len(called)
    time.sleep(0.06)
    assert len(called) == n
    mcp.stop_timers()

