#!/bin/sh
# Package a RoboVM-built .app dir (from :ios:robovmInstall) into an
# UNSIGNED IPA for jailbroken install (AppSync / `ldid -S` on device).
# Usage: package-ipa.sh <path-to-App.app> [output.ipa]
set -e
APP="$1"
OUT="${2:-$(basename "$APP" .app)-armv7-unsigned.ipa}"
[ -d "$APP" ] || { echo "no such .app dir: $APP" >&2; exit 1; }
WORK=$(mktemp -d)
mkdir -p "$WORK/Payload"
cp -r "$APP" "$WORK/Payload/"
(cd "$WORK" && zip -qr "$OLDPWD/$OUT" Payload)
rm -rf "$WORK"
echo "wrote $OUT (UNSIGNED - needs AppSync or on-device ldid -S)"
