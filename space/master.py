#!/usr/bin/env python
# coding: utf-8

# WE ARE THE MASTER CONTROL PROGRAM

import threading
import time
import heapq
from typing import Callable
import logging

log = logging.getLogger(__name__)

from space.living.msg import HasShell
from space.shell import ReadlineShell
from space.shell.mob import Shell as MobShell


class MasterControlProgram:
    """Minimal MCP for local instances.

    For now, supports starting a local interactive shell instance by wiring a
    provided body (owner) and optional prebuilt map/objects. This mirrors what
    lrun-shell.py currently does but centralizes the boot logic here so future
    transports (ssh/telnet) can call the same entry point.
    """

    def __init__(self):
        # lightweight timer scheduler
        self._timer_lock = threading.Lock()
        self._timer_cv = threading.Condition(self._timer_lock)
        self._timer_heap = []  # (when, counter, interval, fn, args, kwargs, label)
        self._timer_counter = 0
        self._timer_thread = None
        self._timers_running = False
        # shared references used by timer tasks
        self.map = None
        self.body = None

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

        # store shared refs so timers see the same objects
        self.map = map
        self.body = body

        # PoC: ensure all non-player HasShell objects have a Mob shell
        if self.map is not None and self.body is not None:
            for obj in self.map.objects:
                if isinstance(obj, HasShell) and obj is not self.body and not isinstance(obj.shell, MobShell):
                    obj.shell = MobShell(owner=obj)

        # ensure timers are available for shells/mobs/daemons
        self.start_timers()
        if self.map is not None:
            # periodically step mob shells on this map
            self.every(4.0, self._step_map_shells)

        shell = ReadlineShell(owner=body, init=init)
        shell.loop()

    # --- Timers -----------------------------------------------------------
    def start_timers(self):
        """Start the background timer loop if not already running.

        Best-effort timing; tasks may run late. Uses a single daemon thread.
        """
        with self._timer_lock:
            if self._timers_running:
                return
            self._timers_running = True
            self._timer_thread = threading.Thread(target=self._timer_loop, name="MCP-Timers", daemon=True)
            self._timer_thread.start()
        log.info("MCP timers started")

    def stop_timers(self):
        """Stop the background timer loop. Tasks remaining will not run."""
        with self._timer_lock:
            if not self._timers_running:
                return
            self._timers_running = False
            self._timer_cv.notify_all()
        # do not join forever in case tests forget; short join
        if self._timer_thread is not None:
            self._timer_thread.join(timeout=0.5)
        log.info("MCP timers stopped")

    def call_out(self, fn: Callable, delay, *args, **kwargs):
        """Schedule a one-shot call roughly after `delay` seconds."""
        return self._schedule(delay, 0.0, fn, args, kwargs, kwargs.pop("label", None))

    def every(self, interval, fn: Callable, *args, **kwargs):
        """Schedule a repeating call roughly every `interval` seconds."""
        return self._schedule(interval, interval, fn, args, kwargs, kwargs.pop("label", None))

    def cancel(self, label):
        """Cancel tasks matching `label`. Best-effort; O(n) prune on next tick."""
        with self._timer_lock:
            if not self._timer_heap:
                return 0
            removed = 0
            # Mark by replacing label with None; actual removal on pop
            for i in range(len(self._timer_heap)):
                when, cnt, interval, fn, args, kwargs, lab = self._timer_heap[i]
                if lab == label:
                    self._timer_heap[i] = (when, cnt, 0.0, None, (), {}, None)
                    removed += 1
            if removed:
                self._timer_cv.notify_all()
            return removed

    def _schedule(self, delay, interval, fn, args, kwargs, label):
        when = time.monotonic() + float(delay)
        with self._timer_lock:
            self._timer_counter += 1
            heapq.heappush(self._timer_heap, (when, self._timer_counter, float(interval), fn, args, kwargs, label))
            self._timer_cv.notify_all()
        self.start_timers()
        return label or (fn, when)

    def _timer_loop(self):
        while True:
            with self._timer_lock:
                if not self._timers_running:
                    return
                now = time.monotonic()
                if not self._timer_heap:
                    self._timer_cv.wait(timeout=0.25)
                    continue
                when, cnt, interval, fn, args, kwargs, label = self._timer_heap[0]
                if when > now:
                    # sleep until next task or short cap
                    timeout = min(when - now, 0.25)
                    self._timer_cv.wait(timeout=timeout)
                    continue
                heapq.heappop(self._timer_heap)

            # Execute outside the lock
            if fn is not None:
                try:
                    fn(*args, **kwargs)
                except Exception:  # pylint: disable=broad-except
                    # Keep the loop alive; logging can be added later.
                    log.exception("Timer task error")

            if interval > 0 and fn is not None:
                # reschedule
                next_when = when + interval
                with self._timer_lock:
                    self._timer_counter += 1
                    heapq.heappush(self._timer_heap, (next_when, self._timer_counter, interval, fn, args, kwargs, label))
                    self._timer_cv.notify_all()

    # --- Helpers ----------------------------------------------------------
    def _step_map_shells(self):
        """Step all shells on a map (best-effort)."""
        log.debug("timer: _step_map_shells")
        # Iterate current snapshot to avoid issues if list mutates during stepping
        if self.map is None:
            return
        for obj in self.map.objects:
            if isinstance(obj, HasShell):
                try:
                    obj.shell.step()
                    log.debug("%s.shell.step()", obj)
                except Exception:  # pylint: disable=broad-except
                    # keep stepping others
                    log.exception("error stepping shell for %s", obj)
