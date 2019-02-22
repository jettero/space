# coding: utf-8

# NOTE: We can't actually use pickle for anything useful it creates big
# outputs, it's slow, and it's inherently insecure I'm using pickle below to
# demonstrate that you *can* reconstruct objects without calling their init

import math
from pickle import Pickler, Unpickler
from io import BytesIO

class A:
    x = 0.5
    def __init_subclass__(cls):
        print(f'init_subclass:A:{cls.__name__}')
    def __init__(self, x=0.7):
        print(f'init:A:{self.__class__.__name__}')
        self.x = min(0.9999999999999999999999999999, abs(x))
        self._orig = (self.x, self.y)
    @property
    def y(self):
        # x**2 + y**2 = 1
        return math.sqrt( 1 - self.x ** 2 )
    def __repr__(self):
        return f'orig: {self._orig} → ({self.x}, {self.y})'

class B(A):
    def __init_subclass__(cls):
        super().__init_subclass__()
        print(f'init_subclass:B:{cls.__name__}')
    def __init__(self, *a, **kw):
        super().__init__(*a,**kw)
        print(f'init:B:{self.__class__.__name__}')

class C(B):
    def __init__(self, *a,**kw):
        super().__init__(*a,**kw)
        print(f'init:C:{self.__class__.__name__}')

a = C(0.2)
a.x = 0.3

fh = BytesIO()
Pickler(fh).dump(a)
fh.seek(0)
_a = Unpickler(fh).load()

print(f' a = {a}')
print(f'_a = {_a}')
