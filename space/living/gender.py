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

    subjective = "it"
    objective = "it"
    possessive = "its"
    reflexive = "itself"


class Male(Gender):
    a = "M"
    s = "male"
    l = "male reproductive modality"

    subjective = "he"
    objective = "him"
    possessive = "his"
    reflexive = "himself"


class Female(Gender):
    a = "F"
    s = "female"
    l = "female reproductive modality"

    subjective = "she"
    objective = "her"
    possessive = "her"
    reflexive = "herself"


class Not(Gender):
    a = "N"
    s = "non reproductive modality"

    subjective = "they"
    objective = "them"
    possessive = "their"
    reflexive = "themself"


class Neuter(Gender):
    a = "0"
    s = "neuter"
    l = "non-gender"

    subjective = "it"
    objective = "it"
    possessive = "its"
    reflexive = "itself"


class Unknown(Neuter):
    a = "U"
    s = "unknown"
    l = "gender unknown"


class GenderNeutral(Gender):
    a = "X"
    s = "neutral"
    l = "gender neutral"

    subjective = "they"
    objective = "them"
    possessive = "their"
    reflexive = "themself"


class Xe(Gender):
    a = "X"
    s = "xe"
    l = "Xe neo-pronoun set"

    subjective = "xe"
    objective = "xem"
    possessive = "xyr"
    reflexive = "xemself"


class Ze(Gender):
    a = "Z"
    s = "ze"
    l = "Ze neo-pronoun set"

    subjective = "ze"
    objective = "hir"
    possessive = "hir"
    reflexive = "hirself"


class Ey(Gender):
    a = "E"
    s = "ey"
    l = "Ey neo-pronoun set"

    subjective = "ey"
    objective = "em"
    possessive = "eir"
    reflexive = "emself"
