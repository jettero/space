# coding: utf-8
"""
the idea here is, you mark a function with a signal like this

    @emits_signal('boo')
    def spooky(...): ...

Then you mark a class with the signal like this

    @subscribes_signal('boo')
    class Whatever:
        def receive_signal(self, emo): ...

Every time a Whatever gets intialized, it's subscribed to the signal.
You can also decorate a function:

    @subscribes_signal('boo')
    def wazzit(emo): ...

The object 'emo' is an Emission, which has the following attributes:
    emo.emitter  # the object that emitted the signal
    emo.signal   # the signal name
"""

import logging
import types, inspect
from .util import weakify

FM = (types.FunctionType, types.MethodType)

log = logging.getLogger(__name__)

__all__ = ["emits_signal", "subscribes_signal"]

SIGNALS = dict()


class Signal:
    class Emission:
        __slots__ = ["emitter", "signal"]

        def __init__(self, signal, emitter):
            log.debug("%s emitting %s", emitter, signal)
            self.emitter = weakify(emitter)
            self.signal = signal.name

    def __init__(self, name, cb=None):
        log.debug("creating %s", self)
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
        unsub = subscriber if isinstance(subscriber, set) else {subscriber}
        log.debug("Signal.unsubscribe(%s ~%s~)", self.name, repr(unsub))
        self.listeners -= unsub

    def emit(self, emitter):
        unsub = set()
        for listener in self.listeners:
            em = self.Emission(self, emitter)
            if isinstance(self.cb, FM):
                log.debug("Emission(%s => %s) =cb()=> %s", repr(emitter), self.name, repr(listener))
                if not self.cb(listener, em):
                    continue
            try:
                if isinstance(listener, FM):
                    log.debug("Emission(%s => %s) =fn()=> %s", repr(emitter), self.name, repr(listener))
                    listener(em)
                else:
                    log.debug("Emission(%s => %s) =Class()=> %s", repr(emitter), self.name, repr(listener))
                    listener.receive_signal(em)
            except TypeError as e:
                log.error("ERROR unsubscribing %s from %s due to type-error: %s", listener, self, e)
                unsub.add(listener)
        if unsub:
            self.unsubscribe(unsub)

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
