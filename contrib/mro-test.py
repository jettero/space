#!/usr/bin/env python
# coding: utf-8

class A:
    def __init__(self, a=0, **kw):
        print('A.__init__')
        self.a = a
        super().__init__(**kw)

class B:
    def __init__(self, b=0, **kw):
        print('B.__init__')
        self.b = b
        super().__init__(**kw)

class C(A, B):
    def __init__(self, c=0, **kw):
        print('C.__init__')
        self.c = c
        super().__init__(**kw)

c = C(a=1, b=2, c=3)
print(f'{c.a}, {c.b}, {c.c}')
