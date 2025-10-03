# coding: utf-8

from .base import Verb


class Action(Verb):
    name = "sheet"
    # Keep 's' free for move direction rewrites; no single-letter alias.
    nick = ["sheet", "stats", "status", "character"]

    def do_sheet(self):
        """Display basic character sheet with core stats."""

        def box(title, body_lines, width=None):
            inner = list(body_lines)
            w = max([len(title)] + [len(s) for s in inner])
            if width is not None:
                w = max(w, width)
            top = "+" + "-" * (w + 2) + "+"
            title_line = "| " + title.center(w) + " |"
            framed = [top, title_line, top]
            for s in inner:
                framed.append("| " + s.ljust(w) + " |")
            framed.append(top)
            return "\n".join(framed)

        # name
        lines = [
            f'{self.long if getattr(self, "long", None) else (self.short if getattr(self, "short", None) else str(self))}'
        ]

        # level/class (class TBD), XP
        # Known Living fields; direct access without getattr/hasattr noise
        level = self.level
        xp = self.xp
        lines.append(f"Level: {level}  XP: {xp}")

        # main stats SCI/DIP/etc
        lines.append(f"SCI: {self.sci}")
        lines.append(f"DIP: {self.dip}")
        lines.append(f"MAR: {self.mar}")
        lines.append(f"ENG: {self.eng}")
        lines.append(f"MOR: {self.mor}")

        # gender, height, weight, initiative, then HP
        lines.append(f"Gender: {self.gender}")
        lines.append(f"Height: {self.height}")
        lines.append(f"Weight: {self.weight}")
        lines.append(f"Initiative: {self.initiative}")
        lines.append(f"HP: {self.hp}")

        # inventory summary: count and mass
        inv = list(self.inventory)
        total_mass = 0
        for it in inv:
            total_mass += getattr(it, "mass", 0)
        # blank line intentionally omitted per request
        lines.append(f"Carrying: {len(inv)} items, {total_mass} mass")

        self.tell(box("Character Sheet", lines))
