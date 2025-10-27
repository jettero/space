# coding: utf-8

from .base import Verb


class Action(Verb):
    name = "inventory"
    nick = ["i", "inv"]

    def do_inventory(self):
        from ..shell.message import BoxMessage

        self.simple_action("$N $vinventory $p stuff.")
        entries = []  # (slot_label, item_name, mass_str)
        # collect primary slot items
        for slot in self.slots:
            # Slot.s is a known attribute for Slots
            sname = slot.s[:-5]
            item = None
            try:
                item = slot.item
            except Exception:
                item = None
            if item is None:
                entries.append((sname, "", ""))
                continue
            # StdObj provides .l and .mass for items; access directly
            iname = item.l
            imass = item.mass
            entries.append((sname, iname, f"{imass}" if imass is not None else ""))
            # include one-level contents if item is a container; indent label
            try:
                contents = list(item)
                for it in contents:
                    sub = it.l
                    sm = it.mass
                    entries.append(("  ", sub, f"{sm}" if sm is not None else ""))
            except Exception:
                pass

        if not entries:
            self.my_action("$N $vare carrying nothing.")
            return

        # compute column widths for alignment; keep colon attached to label
        # Determine display label (with colon) and track indent of child rows
        disp = []  # (disp_label, is_child, name, wstr)
        for label, name, wstr in entries:
            is_child = label == "  "
            disp_label = (label + ":") if not is_child else "  "
            disp.append((disp_label, is_child, name, wstr))

        labelcol_w = max(len(d[0]) for d in disp) if disp else 0
        name_w = max(len(d[2]) for d in disp) if disp else 0

        # format rows with aligned item and weight columns; colon sticks to label
        out = []
        for disp_label, is_child, name, wstr in disp:
            # pad after label+colon to start item column consistently
            padding = " " * (labelcol_w - len(disp_label) + 1)
            if not name:
                # empty slot row: just the label+colon
                line = f"{disp_label}"
            else:
                line = f"{disp_label}{padding}{name.ljust(name_w)}  {wstr}"
            out.append(line.rstrip())
        self.tell(BoxMessage("Inventory", out))
