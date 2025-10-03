#!/usr/bin/env python
# coding: utf-8

class A:
    def __init__(self, **kw):
        print('A.__init__')
        self.a = kw.pop('a', 0)
        super().__init__(**kw)

class B:
    def __init__(self, **kw):
        print('B.__init__')
        self.b = kw.pop('b', 0)
        super().__init__(**kw)

class C(A, B):
    def __init__(self, **kw):
        print('C.__init__')
        self.c = kw.pop('c', 0)
        super().__init__(**kw)

c = C(a=1, b=2, c=3)
print(f'{c.a}, {c.b}, {c.c}')
