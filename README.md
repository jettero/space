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
missions. appserv (Rust) hosts it over SSH.

# Starting it
You need an appserv checkout and a Rust toolchain. Point `APPSERV_DIR` at the
checkout and run `start.sh`:

```
export APPSERV_DIR=/path/to/appserv
./start.sh
```

`start.sh` builds appserv, runs `appserv --install` (which reads
`APPSERV.yaml` and installs `requirements.txt` into appserv's Python) the first
time and again whenever either file changes, then:

- **macOS:** runs the server in the foreground; ^C stops it. `BIND`
  (default `127.0.0.1:2222`) sets the listen address.
- **Linux:** restarts the `space` systemd user unit. Link it once with
  `systemctl --user link $PWD/contrib/space.service`. To override the unit's
  defaults (`SPACE`, `BIND`), copy `contrib/space.env-example` to
  `~/.config/space/env`.

Then connect with `ssh -p 2222 yourname@127.0.0.1`. A new name gets a sign-up
prompt asking for your ssh public key.

Accounts and saves live under `data/` (gitignored): appserv's users in
`data/obj/_/user`, game saves in `data/appserv/space.db`.

For poking at a map without the server, `./lrun-shell.py some.map` loads that
map with just you on it.
