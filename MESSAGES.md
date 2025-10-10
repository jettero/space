# Messaging Guidelines

This project separates message composition from delivery. Use these rules to
choose the right delivery API and to compose tokens consistently.

Delivery APIs
- `tell(msg)`
  - Private, informational output to the actor only.
  - Use for non‑actions: maps (`MapMessage`), boxed summaries (`BoxMessage`), character
    sheets, and similar data views.
- `my_action(msg, *obs)`
  - Private action phrasing to the actor only.
  - Use when the result should not be broadcast but should still use action
    grammar (e.g., “$N $vare carrying nothing.”).
- `simple_action(msg, *obs)`
  - Broadcast an action involving only the actor and (optionally) inanimate
    objects. Sends variants to actor and nearby observers.
  - Example: opening/closing doors, moving, inventorying, looking around.
- `targeted_action(msg, target, *obs)`
  - Broadcast an action that involves another living (`target`). Sends actor,
    target, and others variants.
  - Example: attacking someone, giving to a living, grabbing a living.

Token Composition
- Always tag verbs with `$vverb` so agreement is correct for actor/others.
  - Examples: `$vattack`, `$vopen`, `$vmove`, `$vinventory`, `$vare`.
- Use `$N/$n` for the subject (actor), `$T/$t` for the target living,
  `$O/$o` for inanimate objects.
- Prefer `$t` for livings and `$o` for objects. As a convention,
  `$t` is equivalent to “the first living argument” (`$n1o` in legacy terms).
- Even in `my_action`, use `$v…` and proper `$N/$T/$O` tokens so phrasing is
  consistent and future broadcasts remain correct if behavior changes.

Examples
- Actor opens a door (object): `simple_action("$N $vopen $o.", door)`
- Actor drops an item (object): `simple_action("$N $vdrop $o.", item)`
- Actor picks up a living (rare): `targeted_action("$N $vgrab $t.", living)`
- Actor attacks another living: `targeted_action("$N $vattack $t causing $o damage.", enemy, dmg)`
- Private empty inventory notice:
  `my_action("$N $vare carrying nothing.")`
- Show a map or box:
  `tell(MapMessage(...))`, `tell(BoxMessage(title, lines))`

Notes
- Informational, non‑action content stays `tell()`.
- Use `simple_action` for actor+object actions; `targeted_action` for actor+living actions.
- Always prefer `$t` for livings and `$o` for objects; avoid misusing `$t` for
  objects as that implies a living target.
