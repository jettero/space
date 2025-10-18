# coding: utf-8

import re
from .pv import PV
from .named import Named
from .roll import roll, Roll, RollError


class DN(PV):
    d = "supposedly descriptive number"

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.convert_on_set = getattr(cls.Meta, "convert_on_set", False)
        cls.check_type = getattr(cls.Meta, "check_type", True)

    def __init__(self, value=0, **kw):
        if isinstance(value, str):
            # if m:=re.match('(\d*d\d+(?:\s*[+-]\s*\d*)\s*(.+)', value):
            #     value = f'{roll(m.group(1))} {m.group(2)}'
            try:
                value = roll(value)
            except RollError:
                pass
        elif isinstance(value, Roll):
            value = value.roll()
        super().__init__(value, **kw)

    class Meta:
        units = "dn = []"
        save = "vs\0"

    def __repr__(self):
        return f"<{self}>"


DescriptiveNumber = DN
