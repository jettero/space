# coding: utf-8

from .base import Verb


class Action(Verb):
    name = 'sheet'
    # Keep 's' free for move direction rewrites; no single-letter alias.
    nick = ['sheet', 'stats', 'status', 'character']

    def do_sheet(self):
        """Display basic character sheet with core stats."""
        # core identity
        lines = [
            f'{getattr(self, "long", getattr(self, "short", str(self)))}',
        ]

        # vitals and attributes
        hp = getattr(self, 'hp', None)
        level = getattr(self, 'level', None)
        xp = getattr(self, 'xp', None)
        gender = getattr(self, 'gender', None)

        if hp is not None:
            lines.append(f'HP: {hp}')
        if level is not None:
            lines.append(f'Level: {level}')
        if xp is not None:
            lines.append(f'XP: {xp}')
        if gender is not None:
            lines.append(f'Gender: {gender}')

        # physical stats
        h = getattr(self, 'height', None)
        w = getattr(self, 'weight', None)
        if h is not None:
            lines.append(f'Height: {h}')
        if w is not None:
            lines.append(f'Weight: {w}')

        # skills
        for attr in ('sci', 'dip', 'mar', 'eng', 'mor', 'initiative'):
            v = getattr(self, attr, None)
            if v is not None:
                lines.append(f'{attr.upper()}: {v}')

        # inventory summary: count and mass
        try:
            inv = list(self.inventory)
        except Exception:
            inv = []
        total_mass = 0
        for it in inv:
            try:
                total_mass += it.mass
            except Exception:
                pass
        lines.append(f'Carrying: {len(inv)} items, {total_mass} mass')

        self.tell('\n'.join(lines))
