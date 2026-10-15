# What is this?
I'm trying to write up a game engine that feels vaguely d20 but with its own
mechanics that fit better with a video game than a paper game.

That's the notion anyway.

# Goals
Hopefully whatever game(s) result from this effort will have a Nethack / Angband
/ Shattered Pixel Dungeon feel to them: roguelike, RPG, etc.

The lib is called /space/ because I wanted a generic backend for a SciFi random
map explorer (at least originally) and I just kinda liked the name -- including
the oddball punctuation.

It's a MUD: shared (sharded) space stations, plus instanced ships and away
missions. [appserv](contrib/appserv) (Rust) hosts it over SSH.
