# coding: utf-8

from .pv import PV
from .named import Named
from .roll import roll, Roll, RollError

class DN(PV, Named):
    d = 'supposedly descriptive number'

    a_fmt = '{v:{fmt}} {a}'
    s_fmt = '{v:{fmt}} {s}'
    l_fmt = '{v:{fmt}} {l}'
    d_fmt = '{v:{fmt}} {l} :- {d}'

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.convert_on_set = getattr(cls.Meta, 'convert_on_set', False)
        cls.check_type     = getattr(cls.Meta, 'check_type', True)

    def __init__(self, value=0, **kw):
        if isinstance(value, str):
            try: value = roll(value)
            except RollError: pass
        elif isinstance(value, Roll):
            value = value.roll()
        super().__init__(value, **kw)

    class Meta:
        units = 'dn = []'
        save = 'vs\0'

    def __repr__(self):
        return f'<{self.abbr}>'

    def __str__(self):
        return f'{self.abbr}'

    def __format__(self, spec):
        return Named.__format__(self, spec)

DescriptiveNumber = DN
