# coding: utf-8

import logging
import space.exceptions as E

from space.find import find_verb_method
from space.pv import INFINITY

from ..vv import VV
from ..stdobj import StdObj
from ..container import Containable
from ..damage import Damage, Kinetic
from ..roll import Roll, AttrChoices

from .gender import Gender
from .stats import Sci, Dip, Mar, Eng, Mor, HitPoints, ClassRank, ExperiencePoints, Initiative
from .slots import PackSlot, Slots
from .msg import ReceivesMessages

import space.exceptions as E

log = logging.getLogger(__name__)


class CanMove:
    def move(self, *moves):
        if len(moves) == 1 and isinstance(moves[0], (tuple, list)):
            moves = moves[0]
        c = self.location  # pylint: disable=no-member
        for move in moves:
            c = c.mpos(move)
            c.add_item(self)

    def can_move_words(self, *moves, obj: StdObj = None):
        is_moving = self if obj is None else obj
        if is_moving is None:
            is_moving = self
        c = is_moving.location  # pylint: disable=no-member
        for move in moves:
            c = c.mpos(move)
            try:
                if c.accept(is_moving):
                    continue
            except AttributeError:
                return False, {"error": "there's something in the way"}
            except E.ContainerError as e:
                return False, {"error": e}
        return True, {"moves": moves}  # keys must match do_move_words args

    def can_move_obj_words(self, obj: StdObj, *moves):
        if not obj:
            return False, {"error": "which object?"}
        # the method router calls longest first, so we have a chance to
        # populate is_moving before can_move_words fires
        # XXX: should we do more to consider which obj is more appropriate?
        # XXX: if the obj doesn't want to move, we should have some sort of ability contest here
        if isinstance(obj, (list, tuple)):
            obj = obj[0]
        return True, {"obj": obj}  # keys must match do_move_obj_words args

    def do_move_words(self, *moves):
        log.debug("do_move_words(%s)", moves)
        from ..map.dir_util import moves_to_description

        desc = moves_to_description(moves)
        self.move(*moves)
        self.simple_action(f"$N $vmove {desc}.")

    def do_move_obj_words(self, obj, *moves):
        log.debug("do_move_obj_words(%s, %s)", obj, moves)
        from ..map.dir_util import moves_to_description

        desc = moves_to_description(moves)
        obj.move(*moves)
        self.simple_action(f"$N $vmove $o {desc}.", obj)


class Living(ReceivesMessages, CanMove, StdObj):
    health = gender = None  # autoloaded from metaclass
    active = False

    s = l = "living"
    a = "L"
    d = "a living object"

    # XXX: these should all be computed from our hight and body shape I guess
    reach = 1.42  # arm reach for closing doors and grabbing things
    sight_range = None  # our visual range is forever
    hearing_range = None  # we hear forever too

    @property
    def abbr(self):
        if self.active:
            return "@"
        return super().abbr

    class Choices(AttrChoices):
        _ordered = ("gender", "height", "mass")

        gender = (Gender,)
        height = Roll("5d6+30")
        mass = Roll("6d8+40")
        width = lambda self: self.height * 0.42
        depth = lambda self: (self.mass / "50 kg").v
        health = lambda self: HitPoints("1d6+10")

    def __init__(self, long=None, short=None, **kw):
        self.slots = self.Slots(self)

        if long:
            self.long = long
            if not short:
                if ", " in long:
                    short = long.split(", ")[1]
                elif " " in long:
                    short = long.split()[0]
        if short:
            self.short = short

        self.sci = Sci()
        self.dip = Dip()
        self.mar = Mar()
        self.eng = Eng()
        self.mor = Mor()

        self.initiative = Initiative(self.mar, self.mor, self.mass)
        self.Choices.apply_attrs(self, **kw)

        self.level = ClassRank(1)
        self.xp = ExperiencePoints(0)
        self.damage = Damage()

        super().__init__(**kw)

    @property
    def subjective(self):  # e.g., he/she/they/it
        return self.gender.subjective

    @property
    def objective(self):  # e.g., him/her/them/it
        return self.gender.objective

    @property
    def possessive(self):  # e.g., his/her/their/its
        return self.gender.possessive

    @property
    def reflexive(self):  # e.g., himself/herself/themself/itself
        return self.gender.reflexive

    def hurt(self, damage):
        h1 = self.hp
        self.damage.add(damage)
        log.debug("%s .hurt(%s) hp %s -> %s", self, damage, h1, self.hp)

    @property
    def weapon(self):
        # XXX: we need some way to mount weapons
        # XXX: we need a Weapon base class as well
        return self

    def roll_damage(self):
        # XXX: we probably need a weapon subclass that bodies can inherit from
        # this should be a function of living things also being weapons when
        # employed that way
        return Kinetic(Roll("1d2").roll())

    def attack(self, other):
        # XXX: clearly, we need to send this instruction to a fight daemon to
        # see when the attack happens and whether it succeeds
        # XXX: we should really roll to see if we hit

        w = self.weapon
        d = w.roll_damage()

        # XXX: any time we deliver a message to a player, we should deliver
        # something to all players in view and that should automatically parse
        # context, e.g.: $N $vattack $t causing $o damage.
        self.targeted_action("$N $vattack $t causing $o damage.", other, d)

        log.debug("%s .attack( %s ) weapon=%s damage=%s", self, other, w, d)
        other.hurt(d)

    def unit_vect_to(self, other):
        try:
            op = other.location.pos
        except AttributeError:
            try:
                op = self.location.map.find_obj(other).pos
            except AttributeError:
                op = None
        if op:
            return VV(*self.location.pos) - VV(*op)

    def unit_distance_to(self, other):
        v = self.unit_vect_to(other)
        if v is not None:
            return v.length
        return INFINITY

    def can_attack_living(self, living):
        # candidates are pre-sorted by router; pick first in reach
        for targ in living:
            dist = self.unit_distance_to(targ)
            log.debug("can_attack_living() considering %s at a distance of %s", targ, dist)
            if dist is not None and dist <= self.reach:
                log.debug("  … seems good, returning")
                return (True, {"target": targ})  # "target" is do_attack argument name
        log.debug("  … nothing seemed to match")
        return (False, {"error": "There's no targets with that name in range."})

    def do_attack(self, target):
        self.attack(target)

    def can_look(self):
        # XXX: this accepts any amount of words after 'look'
        return True, {}

    def can_look_living(self):
        return (False, {"error": "XXX: this should work sometimes"})

    def do_look(self):
        from ..shell.message import MapMessage

        self.simple_action("$N $vlook around.")
        self.tell(MapMessage(self.location.map.visicalc_submap(self)))

    @property
    def hp(self):
        return self.health - self.damage

    @property
    def conscious(self):
        return self.hp > 0

    @property
    def unconscious(self):
        return -10 <= self.hp <= 0

    @property
    def alive(self):
        return self.hp >= -10

    @property
    def dead(self):
        return self.hp < -10

    def info(self):
        return "\n".join(
            [
                f"Type:   {self.abbr}",
                f"Gender: {self.gender.short}",
                f"Sci:    {self.sci.v:>2}",
                f"Dip:    {self.dip.v:>2}",
                f"Mar:    {self.mar.v:>2}",
                f"Eng:    {self.eng.v:>2}",
                f"Mor:    {self.mor.v:>2}",
                "",
                f"Level:  {self.level.v} ({self.xp.abbr})",
                f"Health: {self.hp} / {self.health.abbr}",
            ]
        )

    def receive_item(self, item):
        try:
            self.slots.pack.add_item(item)
            return
        except:
            pass
        try:
            self.slots.default = item
            return
        except:
            pass
        for slot in self.slots:
            try:
                slot.add_item(item)
                return
            except:
                pass
        if item.location is not self.location:
            self.location.add_item(item)

    def accept(self, item):
        for slot in self.slots:
            if slot.accept(item):
                return True
        return False

    @property
    def inventory(self):
        return self.slots.inventory

    def do(self, input_text):
        self.shell.do(input_text)

    def can_inventory(self):
        return True, {}

    do_inventory = find_verb_method("inventory", "do_inventory")

    def can_sheet(self):
        return True, {}

    do_sheet = find_verb_method("sheet", "do_sheet")
