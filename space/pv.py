# coding: utf-8

import copy
import operator
import logging

from pint import UnitRegistry, DimensionalityError
from .named import FORMAT_RE

INFINITY = float('inf')
log = logging.getLogger(__name__)

class PVMeta:
    ureg = UnitRegistry()

    def __init_subclass__(cls):
        # set for PV and its subclasses
        definition = cls.Meta.units # pylint: disable=no-member
        if '=' in definition:
            log.debug('defining %s in subclass %s', definition, cls.__name__)
            cls.ureg.define(definition)
        cls.units = definition.split(' ')[0].split('=')[0]
        cls.zero  = (0 * cls.ureg(cls.units))

def _is_qty(x):
    if x.__class__.__name__ != 'Quantity': return False
    if not hasattr(x, 'units'):            return False
    if not hasattr(x, 'magnitude'):        return False
    return True

class PV(PVMeta):
    convert_on_set = False
    check_type     = False

    class Meta:
        units = 'pv = []'

    @classmethod
    def quantify_expression(cls, expression):
        if isinstance(expression, str):
            return cls.ureg.parse_expression(expression)
        if isinstance(expression, (int,float)):
            return expression * cls.zero.units
        if _is_qty(expression):
            return copy.copy(expression)
        if isinstance(expression, PV):
            return copy.copy(expression._q) # pylint: disable=protected-access
        raise TypeError(f'unable to quantify_expression({repr(expression)})')

    @classmethod
    def fix_dimensionless(cls, qty):
        if qty.dimensionless:
            return qty.magnitude * cls.zero.units
        return qty

    @property
    def q(self):
        return self._q

    @q.setter
    def q(self, expression):
        fix = self.fix_dimensionless(self.quantify_expression(expression))
        if self.convert_on_set:
            self._q = self.zero + fix
        elif self.check_type:
            self._q = fix + self.zero
        else:
            self._q = fix

    def __init__(self, expression=None):
        self._q = self.zero
        self.q = expression

    def __repr__(self):
        return f'PV<{self}>' # invoke __format__

    def __str__(self):
        return f'{self}' # invoke __format__

    def __format__(self, spec):
        if spec in ('a', 'abbr'):
            return self._q.__format__('~P')
        if spec in ('s', 'short'):
            return self._q.__format__('~')
        if spec in ('l', 'long'):
            return self._q.__format__('')
        m = FORMAT_RE.match(spec)
        if m:
            fmt, m_select = m.groups()
            if not m_select:
                m_select = 'a'
            else:
                m_select = m_select.lower().strip()[0]
            if   m_select == 'a':
                spec = '~P'
            elif m_select == 's':
                spec = '~'
            elif m_select == 'l':
                spec = ''
            else:
                spec = '~P'
            if fmt:
                spec = fmt + spec
        return self._q.__format__(spec)

    def clone(self):
        return self.__class__(self._q)

    @property
    def v(self):
        return self._q.magnitude

    @property
    def s(self):
        return f'{self._q.units:~}'
    @property
    def a(self):
        return f'{self._q.units:~P}'
    @property
    def l(self):
        return f'{self._q.units}'

    @a.setter
    def a(self,v):
        self._q = PV(f'0 {v}') + self._q
    @s.setter
    def s(self,v):
        self._q = PV(f'0 {v}') + self._q
    @l.setter
    def l(self,v):
        self._q = PV(f'0 {v}') + self._q

    def __radd__(self, other):
        return self + other

def dimensionless(x):
    if isinstance(x, (int,float)):
        return True
    try:
        if x.dimensionless:
            return True
    except AttributeError:
        pass
    return False

def magnitude(x):
    try: return x.magnitude
    except AttributeError: pass
    if not isinstance(x, (int,float)):
        return x.v
    return x

def generic_value(other):
    try: return other._q # pylint: disable=protected-access
    except AttributeError: pass
    if isinstance(other, str):
        return PV(other)._q # pylint: disable=protected-access
    try: return other.v
    except AttributeError: pass
    return other

def common_class(this, other, last_resort=PV):
    st = type(this)
    if isinstance(other, st):
        return st
    ot = type(other)
    for p in ((st,ot), (ot,st)):
        try:
            c = p[0].affinity_class(p[1])
            if c:
                return c
        except AttributeError:
            pass
    for sm in st.mro():
        if not issubclass(sm, PV):
            break
        for om in ot.mro():
            if not issubclass(om, PV):
                break
            if isinstance(this, om) and isinstance(other, sm):
                return sm
    return last_resort

def add_boolops(cls, *op):
    def _helper(op): # pylint: disable=invalid-name
        op_f = getattr(operator, op)
        def _inner(self, other):
            gv = generic_value(other)
            if isinstance(gv, (int,float)):
                gv *= self._q.units # pylint: disable=protected-access
            return bool( op_f(self._q, gv) ) # pylint: disable=protected-access
        return _inner
    for i in [ f'__{x}__' for x in op ]:
        setattr(cls, i, _helper(i))


def add_binops(cls, *op):
    def _helper(op): # pylint: disable=invalid-name
        op_f = getattr(operator, op)
        def _inner(self, other):
            ccls = common_class(self, other)
            gv = generic_value(other)
            # this is more complciated than it looks
            # PV('3g')*3 gives 9 grams without the below kludging
            # PV('3g')+3 requires the extra tweak below to give 6 grams
            # … 3g + 3 is not 6g … we *make* this work for sanity, but it's
            # wrong and arguably quite stupid … but it works
            # 1. try to do the op_f()
            # 2. if we have a dimensionality problem
            #   a. if gv is somehow dimensionless (aka unit-less)
            #   b. try to find the magnitude and pretend it's self.units
            try:
                v = op_f(self._q, gv) # pylint: disable=protected-access
            except DimensionalityError:
                if dimensionless(gv):
                    ccls = self.__class__
                    v = op_f(self._q, magnitude(gv) * self._q.units) # pylint: disable=protected-access
                else:
                    raise
            except Exception as e:
                raise Exception(f'op={op} error (v-conversion)') from e
            # And lastly, if the calculation produces valid units that aren't compatible
            # with the chosen common class (ccls), return a PV of the new quantity
            try:
                return ccls(v)
            except DimensionalityError:
                return PV(v)
            except TypeError as e:
                return PV(v)
            except Exception as e:
                raise Exception(f'op={op} error (ccls={ccls} v={v})') from e
        return _inner
    for i in op:
        setattr(cls, f'__{i}__', _helper(i))

def add_urnops(cls, *op):
    def _helper(op): # pylint: disable=invalid-name
        op_f = getattr(operator, op)
        def _inner(self):
            return self.__class__( op_f(self._q) ) # pylint: disable=protected-access
        return _inner
    for i in op:
        setattr(cls, f'__{i}__', _helper(i))

add_boolops(PV, 'lt', 'le', 'eq', 'ne', 'ge', 'gt')
add_binops(PV, 'add', 'sub', 'mul', 'floordiv', 'truediv', 'mod', 'pow')
add_urnops(PV, 'neg', 'abs')
