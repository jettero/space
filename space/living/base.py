# coding: utf-8

import logging
import space.exceptions as E

from ..vv        import VV
from ..obj       import baseobj
from ..container import Containable
from ..damage    import Damage, Kinetic
from ..roll      import Roll, AttrChoices

from .gender import Unknown
from .stats  import Sci, Dip, Mar, Eng, Mor, HitPoints, ClassRank, ExperiencePoints, Initiative
from .slots  import PackSlot, Slots

import space.exceptions as E

log = logging.getLogger(__name__)

class HasShell:
    _shell = None

    @property
    def shell(self):
        if self._shell is None:
            from ..shell.log import Shell as LogShell
            self._shell = LogShell(owner=self)
        return self._shell

    @shell.setter
    def shell(self, v):
        from ..shell.base import BaseShell
        if v is None:
            self._shell = v
        if not isinstance(v, BaseShell):
            raise E.STypeError(f'{v} is not a shell')
        self._shell = v

    def tell(self, msg):
        self.shell.receive(msg)

class CanMove:
    def move(self, *moves):
        if len(moves) == 1 and isinstance(moves[0], (tuple,list)):
            moves = moves[0]
        c = self.location # pylint: disable=no-member
        for move in moves:
            c = c.mpos(move)
            c.add_item(self)

    def can_move_words(self, *moves, obj:Containable=None):
        is_moving = self if obj is None else obj
        if is_moving is None:
            is_moving = self
        c = is_moving.location # pylint: disable=no-member
        for move in moves:
            c = c.mpos(move)
            try:
                if c.accept(is_moving):
                    continue
            except AttributeError:
                return False, {'error': "there's something in the way" }
            except E.ContainerError as e:
                return False, {'error': e}
        return True, {'moves': moves}

    def can_move_obj_words(self, obj:Containable, *moves):
        if not obj:
            return False, {'error': 'which object?'}
        # the method router calls longest first, so we have a chance to
        # populate is_moving before can_move_words fires
        # XXX: should we do more to consider which obj is more appropriate?
        # XXX: if the obj doesn't want to move, we should have some sort of ability contest here
        if isinstance(obj, (list,tuple)):
            obj = obj[0]
        return True, {'obj': obj}

    def do_move_words(self, *moves):
        log.debug('do_move_words(%s)', moves)
        self.move(*moves)

    def do_move_obj_words(self, obj, *moves):
        log.debug('do_move_obj_words(%s, %s)', obj, moves)
        obj.move(*moves)

class Living(Containable, HasShell, CanMove, baseobj):
    health = gender = None # autoloaded from metaclass
    active = False

    s = l = 'living'
    a = 'L'
    d = 'a living object'

    @property
    def abbr(self):
        if self.active:
            return '@'
        return super().abbr

    class Slots(Slots):
        class Meta:
            slots = {'pack': PackSlot}
            default = 'pack'

    class Choices(AttrChoices):
        _ordered = ('gender', 'height', 'mass')

        gender = (Unknown,)
        height = Roll('5d6+30')
        mass   = Roll('6d8+40')
        width  = lambda self: self.height * 0.42
        depth  = lambda self: (self.mass / '50 kg').v
        health = lambda self: HitPoints('1d6+10')

    def __init__(self, long=None, short=None):
        super().__init__()
        self.slots = self.Slots(self)

        if long:
            self.long = long
            if not short:
                if ', ' in long:
                    short = long.split(', ')[1]
                elif ' ' in long:
                    short = long.split()[0]
        if short:
            self.short = short

        self.sci = Sci()
        self.dip = Dip()
        self.mar = Mar()
        self.eng = Eng()
        self.mor = Mor()

        self.initiative = Initiative(self.mar, self.mor, self.mass)
        self.Choices.apply_attrs(self)

        self.level = ClassRank(1)
        self.xp = ExperiencePoints(0)
        self.damage = Damage()

    def hurt(self, damage):
        h1 = self.hp
        self.damage.add(damage)
        log.debug('%s .hurt(%s) hp %s -> %s', self, damage, h1, self.hp)

    @property
    def weapon(self):
        # XXX: we need some way to mount weapons
        # XXX: we need a Weapon base class as well
        return self

    def roll_damage(self):
        # XXX: we probably need a weapon subclass that bodies can inherit from
        # this should be a function of living things also being weapons when
        # employed that way
        return Kinetic(Roll('1d2').roll())

    def attack(self, other):
        # XXX: clearly, we need to send this instruction to a fight daemon to
        # see when the attack happens and whether it succeeds
        # XXX: we should really roll to see if we hit

        w = self.weapon
        d = w.roll_damage()

        # XXX: any time we deliver a message to a player, we should deliver
        # something to all players in view and that should automatically parse
        # context, e.g.: $N $vattack $t causing $o damage.
        self.tell(f'You attack {other} causing {d} damage.')
        other.tell(f'{self} attacks you causing {d} damage')

        log.debug('%s .attack( %s ) weapon=%s damage=%s', self, other, w, d)
        other.hurt(d)

    def unit_vect_to(self, other):
        try:
            op = other.location.pos
        except AttributeError:
            try:
                op = self.location.map.find_obj(other).pos
            except AttributeError:
                pass
        if op:
            return VV(*self.location.pos) - VV(*op)

    def unit_distance_to(self, other):
        v = self.unit_vect_to(other)
        if v:
            return v.length

    def can_attack_living(self, living):
        # XXX: weapons should have a range or reach or something; instead, we
        # use 1.42 as "adjacent"
        for dist,targ in sorted([ (self.unit_distance_to(o), o) for o in living ]):
            log.debug('can_attack_living() considering %s at a distance of %s', targ, dist)
            if dist <= 1.42:
                log.debug('  … seems good, returning')
                return (True, {'target': targ})
        log.debug('  … nothing seemed to match')
        return (False, {'error': "There's no targets with that name in range."})

    def do_attack(self, target):
        self.attack(target)

    def can_look(self):
        # XXX: this accepts any amount of words after 'look'
        return True, {}

    def can_look_living(self):
        return (False, {'error': "XXX: this should work sometimes"})

    def do_look(self):
        from ..shell.message import MapMessage
        self.tell(MapMessage(self.location.map.visicalc_submap(self)))
        self.tell('You look around.')

    @property
    def hp(self):
        return self.health - self.damage

    @property
    def conscious(self):
        return self.hp > 0

    @property
    def dead(self):
        return self.hp < -10

    def info(self):
        return '\n'.join([
            f'Type:   {self.a}',
            f'Gender: {self.gender.short}',
            f'Sci:    {self.sci.v:>2}',
            f'Dip:    {self.dip.v:>2}',
            f'Mar:    {self.mar.v:>2}',
            f'Eng:    {self.eng.v:>2}',
            f'Mor:    {self.mor.v:>2}',
            '',
            f'Level:  {self.level.v} ({self.xp.abbr})',
            f'Health: {self.hp} / {self.health.abbr}',
        ])

    @property
    def pack(self):
        return self.slots.default

    @pack.setter
    def pack(self, v):
        self.slots.default = v

    def receive_item(self, item):
        c = self.pack
        if c is None:
            raise E.STypeError(f'{self} does not have a default container')
        c.add_item(item)

    def do(self, input_text):
        self.shell.do(input_text)
