#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
exec python3 -m jeli.server --host 127.0.0.1 --port "${JELI_PORT:-8787}"
