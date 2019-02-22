# coding: utf-8

import weakref
from ...named import Tags
from ..dir_util import translate_dir, DDIRS, reverse_dir, orthoganal_dirs

class MapObj:
    _map = _pos = None

    # NOTE: we define the MapObj.box property during import space.map.util
    # e.g.: self.box → Box(MapObj)

    def __init__(self, mobj=None, pos=None):
        self.map = mobj
        self.pos = pos

        self.tags = Tags()

    def __bool__(self):
        return True

    def clone(self, mobj=None, pos=None):
        return self.__class__(mobj=mobj, pos=pos)

    @property
    def abbr(self):
        return getattr(self, 'a', '?')

    def __repr__(self):
        # NOTE: kinda fucked up...  we used to return f'{self}#{id(self):02x}'
        # but the {self} was binding to the wrong object or something and
        # returning totally the wrong stringification.  Probably a python bug
        # that I'll never be able to reproduce for a report so just invoke
        # str(self) and be done with it.
        return f'{str(self)}#{id(self):02x}'

    def __str__(self):
        return f'{self.__class__.__name__}[{self.pos}]'

    @property
    def pos(self):
        ''' our position in the map '''
        return self._pos

    def dpos(self, dir_name):
        ''' the position of the cell in the direction `dir_name` '''
        return translate_dir(dir_name, self.pos)

    def r_dpos(self, dir_name):
        ''' reversed direction (n → s) of dpos() '''
        return translate_dir(reverse_dir(dir_name), self.pos)

    def mpos(self, dir_name):
        ''' the map object in the direction `dir_name` '''
        try: return self.map[self.dpos(dir_name)]
        except ValueError: pass

    def r_mpos(self, dir_name):
        ''' reversed direction (n → s) of mpos() '''
        try: return self.map[self.r_dpos(dir_name)]
        except ValueError: pass

    def istype(self, of_type=None):
        ''' is this cell of type `of_type` (or simply True if of_type is None) '''
        if of_type is None:
            return True
        return isinstance(self, of_type)

    def dtype(self, dir_name, of_type=None):
        ''' cell.dtype(dir_name, of_type=types_here)
            means: is the cell in the `dir_name` direction of the same type
            as (by default) myself? '''
        if of_type is None:
            of_type = self.__class__
        # NOTE: we do this longhand so cell.dtype('n', type(None)) returns
        # False when out of bounds — and we rely on this in map generation
        p = self.dpos(dir_name)
        if self.map.in_bounds(*p):
            return isinstance(self.map[p], of_type)
        return False

    def r_dtype(self, dir_name, of_type=None):
        ''' reversed direction (n → s) of dtype() '''
        return self.dtype( reverse_dir(dir_name), of_type=of_type )

    def od_dtype(self, dir_name, of_type=None, either=True):
        ''' True if either of the orthoganal dirs of `dir_name` is `of_type`
            example: self.od_dtype('n', of_type=Cell) is true when either or
            of the w-cell and the e-cell are of type Cell

            additionally, set `either` to False to indicate that both cells
            must be `of_type` for the method to return True
        '''
        d1, d2 = orthoganal_dirs(dir_name)
        if self.dtype(d1, of_type=of_type):
            if either:
                return True
            d1 = True
        if self.dtype(d2, of_type=of_type):
            if either:
                return True
            d2 = True
        return d1 is True and d2 is True

    @pos.setter
    def pos(self, v):
        if v is None:
            self._pos = None
        else:
            # we do want this to generate an error if v isn't the right shape
            self._pos = (v[0], v[1])

    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, v):
        if v is not None:
            v = weakref.proxy(v)
        self._map = v

    def iter_neighbors(self, dirs='nsew', of_type=None):
        if of_type is None:
            of_type = MapObj
        for d in dirs:
            m = self.mpos(d)
            if isinstance(m, of_type):
                yield (d,m)

    def has_neighbor(self, of_type=None):
        for _ in self.iter_neighbors(of_type=of_type):
            return True
        return False

    def neighbor_dict(self, of_type=None):
        return { k:v for k,v in self.iter_neighbors(of_type=of_type) }

    def neighbors(self, of_type=None):
        return [ v for k,v in self.iter_neighbors(of_type=of_type) ]

    @property
    def visible(self):
        return 'can_see' in self.tags

    @visible.setter
    def visible(self, v):
        if v: self.tags.add('can_see')
        else: self.tags.remove('can_see')

    @property
    def concealed(self):
        return 'can_see' not in self.tags

    @concealed.setter
    def concealed(self, v):
        if v: self.tags.remove('can_see')
        else: self.tags.add('can_see')

def _get_set_dir(dir_name):
    def _g(self):
        try: t = translate_dir(dir_name, self.pos)
        except ValueError: return
        return self.map[t]
    def _s(self, v):
        self.map[translate_dir(dir_name, self.pos)] = v
    return property(_g).setter(_s)

for _d in DDIRS:
    setattr(MapObj, _d, _get_set_dir(_d))
del _d
