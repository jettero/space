# coding: utf-8

from space.map.dir_util import (
    translate_dir,
    move_string_to_dirs,
    is_direction_string
)

def test_is_direction_string():
    valid_strings = (
        'n', '2n', 'nsew', '2w2n2e',
        'SWne2SW', '2ese, 2SW',
    )
    more_valid_strings = (
        ', '.join(valid_strings),
        ''.join(valid_strings),
        ' '.join(valid_strings),
    )

    for s in valid_strings + more_valid_strings:
        assert is_direction_string(s) is True

def test_trans():
    p = 1,1

    assert translate_dir('w', p) == (0,1)
    assert translate_dir('n', p) == (1,0)
    assert translate_dir('s', p) == (1,2)
    assert translate_dir('e', p) == (2,1)

    assert translate_dir('nw', p) == (0,0)
    assert translate_dir('ne', p) == (2,0)
    assert translate_dir('sw', p) == (0,2)
    assert translate_dir('se', p) == (2,2)

def test_mstd():
    def mstd(x):
        return tuple(move_string_to_dirs(x))
    assert mstd('north, south, east, west')  == ('n','s','e','w')
    assert mstd('2north-east, , east, west') == ('ne', 'ne', 'e', 'w')
    assert mstd('2 south 2n3 e4w') == ('s',)*2 + ('n',)*2 + ('e',)*3 + ('w',)*4
    assert mstd('4n3e') == ('n',)*4 + ('e',)*3
