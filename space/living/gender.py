# coding: utf-8

from ..named import Named

# XXX: what about females with a dick? this module is very 2015 I have
# literally no idea how to fix this. Mechanically, the mudlib is only concerned
# with 'sex', if it's concerned with it at all. For gender, we just leave the
# pronouns super flexible for players that need this and pretend gender is a
# reproductive modality?

class Gender(Named):
    a = "U"
    s = "unknown"
    l = "unknown reproductive modality"

class Male(Gender):
    a = "M"
    s = "male"
    l = "male reproductive modality"


class Female(Gender):
    a = "F"
    s = "female"
    l = "female reproductive modality"


class Other(Gender):
    a = "O"
    s = "other"
    l = "other reproductive modality"

class Not(Gender):
    a = "N"
    s = "not applicable"
