# coding: utf-8

import logging
import weakref

log = logging.getLogger(__name__)

class Signal:
    class Emission:
        def __init__(self, signal, emitter):
            log.debug('emitting signal[%s]', signal.name)
            self.emitter = weakref.proxy(emitter)
            self.signal  = weakref.proxy(signal)

    def __init__(self, name, cb=None):
        log.debug('creating signal[%s]', name)
        self.cb = cb
        self.name = name
        self.listeners = set()

    def subscribe(self, subscriber):
        if not hasattr(subscriber, 'tell'):
            raise TypeError(f'{subscriber} cannot subscribe to {self} (no .tell() method)')
        self.listeners.add(subscriber)

    def unsubscribe(self, subscriber):
        self.listeners -= {subscriber,}

    def emit(self, emitter):
        em = self.Emission(self, emitter)
        for listener in self.listeners:
            if callable(self.cb):
                if not self.cb(listener, emitter):
                    continue
            try:
                listener.tell(em)
            except ReferenceError:
                continue

SIGNALS = dict()

def get_signal(name, cb=None):
    if name in SIGNALS:
        return SIGNALS[name]
    sig = SIGNALS[name] = Signal(name, cb=cb)
    return sig

def subscribes_signal(name, cb=None):
    sig = get_signal(name, cb=cb)
    def decorator(cls):
        def initer(*a, **kw):
            o = cls(*a, **kw)
            sig.subscribe(o)
            return o
        return initer
    return decorator

def emits_signal(name, cb=None):
    sig = get_signal(name, cb=cb)
    def decorator(wrapped):
        def helper(self, *a, **kw):
            sig.emit(self)
            return wrapped(self, *a, **kw)
        return helper
    return decorator
