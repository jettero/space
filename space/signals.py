# coding: utf-8

# the idea here is, you mark a function with a signal like this
#
# @emits_signal('boo')
# def spooky(...): ...
#
# Then you mark a class with the signal like this
#
# @subscribes_signal('boo')
# class Whatever:
#   pass
#
# every time a Whatever gets intialized, it's subscribed to the signal

import logging
import types, inspect
from .util import weakify

FM = (types.FunctionType, types.MethodType)

log = logging.getLogger(__name__)

__all__ = ["emits_signal", "subscribes_signal"]

SIGNALS = dict()


class Signal:
    class Emission:
        def __init__(self, signal, emitter, listener):
            log.debug("%s emitting signal[%s] to %s", emitter, signal.name, listener)
            self.emitter = weakify(emitter)
            self.signal = weakify(signal)
            self.listener = weakify(listener)

    def __init__(self, name, cb=None):
        log.debug("creating signal[%s]", name)
        self.cb = cb
        self.name = name
        self.listeners = set()

    def subscribe(self, subscriber):
        if isinstance(subscriber, FM):
            log.debug("Signal.subscribe(%s =fn()=> %s)", self.name, repr(subscriber))
            self.listeners.add(subscriber)
        elif hasattr(subscriber, "receive_signal"):
            log.debug("Signal.subscribe(%s =Class()=> %s)", self.name, repr(subscriber))
            self.listeners.add(subscriber)
        else:
            raise TypeError(f"{subscriber} cannot subscribe to {self} (no .receive_signal() method)")

    def unsubscribe(self, subscriber):
        self.listeners -= {subscriber}

    def emit(self, emitter):
        for listener in self.listeners:
            em = self.Emission(self, emitter, listener)
            if isinstance(self.cb, FM):
                log.debug("Emission(%s => %s) =cb()=> %s", repr(emitter), self.name, repr(listener))
                if not self.cb(listener, em):
                    continue
            if isinstance(listener, FM):
                log.debug("Emission(%s => %s) =fn()=> %s", repr(emitter), self.name, repr(listener))
                listener(em)
            else:
                log.debug("Emission(%s => %s) =Class()=> %s", repr(emitter), self.name, repr(listener))
                listener.receive_signal(em)

    def __repr__(self):
        return f"signal[{self.name}]"


def get_signal(name, cb=None):
    if name in SIGNALS:
        return SIGNALS[name]
    sig = SIGNALS[name] = Signal(name, cb)
    return sig


def subscribes_signal(name, cb=None):
    sig = get_signal(name, cb)

    log.debug("@subscribes_signal(%s, cb=%s) =generate-decorator=> %s", name, repr(cb), repr(sig))

    def decorator(cls_or_function_or_method):
        if inspect.isclass(cls_or_function_or_method):
            log.debug("@subscribes_signal(%s, cb=%s) => %s", name, repr(cb), repr(cls_or_function_or_method))

            def FakeClass(*a, **kw):
                o = cls_or_function_or_method(*a, **kw)
                log.debug(
                    "@subscribes_signal(%s, cb=%s) =cls=> %s =init=> %s",
                    name,
                    repr(cb),
                    repr(cls_or_function_or_method),
                    repr(o),
                )
                sig.subscribe(o)
                return o

            return FakeClass

        if isinstance(cls_or_function_or_method, FM):
            log.debug("@subscribes_signal(%s, cb=%s) =f=> %s", name, repr(cb), repr(cls_or_function_or_method))
            sig.subscribe(cls_or_function_or_method)
            return cls_or_function_or_method

        raise TypeError(f"can't decorate {cls_or_function_or_method!r} with @subscribes_signal")

    return decorator


def emits_signal(name, cb=None):
    sig = get_signal(name, cb)

    log.debug("@emits_signal(%s, cb=%s) =generate-decorator=> %s", name, repr(cb), repr(sig))

    def decorator(wrapped):
        log.debug("@emits_signal(%s, cb=%s) => %s", name, repr(cb), repr(wrapped))

        def helper(self, *a, **kw):
            sig.emit(self)
            return wrapped(self, *a, **kw)

        return helper

    return decorator
