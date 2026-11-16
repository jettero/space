#!/usr/bin/env bash
# start the space ssh game host: through systemd --user on Linux, in the foreground everywhere else (macOS)
#
# needs APPSERV_DIR, an appserv checkout. On macOS BIND (default 127.0.0.1:2222)
# picks the listen address; on Linux the space.service unit sets it.

trap "exit 1" INT
cd "$(dirname "$0")" || exit 1

: "${APPSERV_DIR:?set APPSERV_DIR to your appserv checkout}"
BIND="${BIND:-127.0.0.1:2222}"
appserv="$APPSERV_DIR/target/debug/appserv"

cargo build --manifest-path "$APPSERV_DIR/Cargo.toml" || exit 2

mkdir -p data
if [ requirements.txt -nt data/.space-deps ] || [ APPSERV.yaml -nt data/.space-deps ]; then
    "$appserv" --install "$PWD" --prefix "$PWD/data" || exit 3
    date > data/.space-deps
fi

if [ "$(uname -s)" = Linux ]; then
    systemctl --user set-environment APPSERV_DIR="$APPSERV_DIR"
    exec systemctl --user restart space
fi

exec "$appserv" "$PWD" --prefix "$PWD/data" --bind "$BIND"
