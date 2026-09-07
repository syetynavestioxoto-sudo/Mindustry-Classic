#!/bin/sh
# Build sbingner/ldid for Linux (RoboVM 2.3.0 ships a macOS-only ldid that
# it uses for jailbreak pseudo-signing; replace it with this one).
# Usage: build-ldid.sh <outdir>   -> <outdir>/ldid
set -e
OUT="$1"
[ -n "$OUT" ] || { echo "usage: $0 <outdir>" >&2; exit 1; }
mkdir -p "$OUT"
if [ ! -d /tmp/ldid-src ]; then
    git clone --depth 1 https://github.com/sbingner/ldid.git /tmp/ldid-src
fi
cd /tmp/ldid-src
git submodule update --init --recursive
make -j"$(nproc)"
cp ldid "$OUT/ldid"
"$OUT/ldid" 2>&1 | head -1
echo "ldid ready at $OUT/ldid"
