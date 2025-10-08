#!/usr/bin/env python
# coding: utf-8

# WE ARE THE MASTER CONTROL PROGRAM

from space.living.msg import HasShell
from space.shell import ReadlineShell


class MasterControlProgram:
    """Minimal MCP for local instances.

    For now, supports starting a local interactive shell instance by wiring a
    provided body (owner) and optional prebuilt map/objects. This mirrors what
    lrun-shell.py currently does but centralizes the boot logic here so future
    transports (ssh/telnet) can call the same entry point.
    """

    def start_instance(self, type="local", username=None, map=None, body=None, init=None):  # pylint: disable=redefined-builtin
        """Start an instance.

        Args:
            type: instance type; only 'local' supported for now.
            username: informational; unused for now.
            map: optional map to render on look; can be None.
            body: the Living to own the shell; required.
            init: list/tuple of initial commands.
        """
        if type != "local":
            raise NotImplementedError("only local instances supported")
        if not isinstance(body, HasShell):
            raise ValueError("body is required to start instance")

        shell = ReadlineShell(owner=body, init=init)
        shell.loop()
