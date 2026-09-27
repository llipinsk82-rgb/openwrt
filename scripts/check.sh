#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

python3 -m unittest discover -s tests -v

if command -v node >/dev/null 2>&1; then
    find luci-theme-archer luci-app-archer-dashboard -type f -name '*.js' -print0 2>/dev/null |
        xargs -0 -r -n1 node --check
fi
