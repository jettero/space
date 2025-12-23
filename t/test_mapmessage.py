import os
import pytest


def has_terminal():
    try:
        os.get_terminal_size()
        return True
    except OSError:
        return False


@pytest.mark.skipif(not has_terminal(), reason="requires terminal (run with: pytest --capture=no)")
def test_mapmessage_rendering(me, a_map):
    from space.shell.prompt import Shell
    from space.msg import MapMessage
    from space.find import set_this_body

    # Replace the list shell with a prompt shell for terminal size
    me.shell = Shell.__new__(Shell)

    # Set this_body
    set_this_body(me)

    # Create visicalc submap - this creates a MapView with LOS filtering
    submap = a_map.visicalc_submap(me)

    # Create MapMessage - this should create display-bounded view
    msg = MapMessage(submap)

    # This should fail with "list index out of range" before the fix
    # because we'd be creating a MapView of a MapView with bounds that
    # extend beyond the original map
    text = msg.map_drawing_text(color=False)
    assert isinstance(text, str)
    assert len(text) > 0

    # Verify the output is actually bounded (not the full map)
    lines = text.strip().split("\n")
    cols, rows = me.shell.terminal_size
    max_display_rows = int(rows * 0.8)
    # The map should be clipped to terminal size, not the full LOS
    assert len(lines) <= max_display_rows + 5  # +5 for some tolerance
