# coding: utf-8
# pylint: disable=invalid-name,protected-access

import pytest
from space.pv import PV, DimensionalityError, INFINITY

def test_infinity():
    pinf = PV(INFINITY)
    assert pinf + 3 == pinf
    assert pinf - 3 == pinf

def test_ops():
    m = PV('195 lb')
    a = PV('9.8 m/s/s')
    f = m*a
    t = PV('13 s')
    v = a*t
    x = a*t**2 * 0.5

    z = PV('0 kg*m/s/s') + f

    f2 = f
    f2 *= 2

    # check to make sure the ops return new objects
    assert f2 is not f
    assert f is not z
    assert f is not m
    assert f is not a

    # check the properties and values and things
    assert pytest.approx( z.v, rel=0.5) == 867
    assert z.l == 'kilogram * meter / second ** 2'
    assert z.s == 'kg * m / s ** 2'
    assert z.a == 'kg·m/s²'
    assert pytest.approx( v.v, rel=0.5 ) == 127
    assert pytest.approx( x.v, rel=0.5 ) == 828

def test_assigns():
    a = PV('32 m/s/s')
    b = PV(a)
    c = PV(a._q)

    assert a is not b
    assert a is not c
    assert b is not c

    assert a._q is not b._q
    assert a._q is not c._q
    assert b._q is not c._q

    class wut(PV):
        class Meta: units = 'shit = [wut] = S'

    assert wut(7) == PV('7 shit')

def test_mismatch():
    m = PV('3g')
    l = PV('3m')
    with pytest.raises(DimensionalityError) as exde:
        m + l # pylint: disable=pointless-statement
    sev = str(exde.value)
    assert '[length]' in sev
    assert '[mass]' in sev

    assert (m + 3) == PV('6g')


def test_lt_z():
    three = PV('3g')
    zero  = PV('0g')

    assert three > 0
    assert zero == 0

def test_format():
    v1 = PV('3.23234 m*m*m')
    assert f'{v1:a}' == '3.23234 m³'
    assert f'{v1:s}' == '3.23234 m ** 3'
    assert f'{v1:l}' == '3.23234 meter ** 3'
    assert f'{v1:0.1fa}' == '3.2 m³'
    v2 = PV('3 m³')
    assert f'{v2:0.1fa}' == '3.0 m³'
