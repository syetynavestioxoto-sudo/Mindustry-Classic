#!/bin/sh
# Fetch the iOS SDK (theos CaviarDreams? no: theos/sdks) and assemble the
# fake Xcode tree:
#   $FAKEXCODE/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS10.3.sdk
# SDK 10.3 is the newest theos SDK that still ships the armv7 slice in
# tapi-tbd-v2 format (parseable by our Apple ld64). Deployment target
# stays 8.0 via -miphoneos-version-min / MinimumOSVersion.
set -e
: "${FAKEXCODE:?FAKEXCODE not set}"
SDK_SRC="${SDK_SRC:-https://github.com/theos/sdks.git}"
DEST="$FAKEXCODE/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs"
mkdir -p "$DEST"
if [ ! -d /tmp/theos-sdks-cache ]; then
    git clone --depth 1 --filter=blob:none --sparse "$SDK_SRC" /tmp/theos-sdks-cache
fi
git -C /tmp/theos-sdks-cache sparse-checkout set iPhoneOS10.3.sdk
rm -rf "$DEST/iPhoneOS10.3.sdk"
cp -r /tmp/theos-sdks-cache/iPhoneOS10.3.sdk "$DEST/iPhoneOS10.3.sdk"
# restore symbols the trimmed theos stubs omit (see patch-sdk.py)
python3 "$(dirname "$0")/patch-sdk.py" "$DEST/iPhoneOS10.3.sdk"
grep -m1 'tapi-tbd' "$DEST/iPhoneOS10.3.sdk/usr/lib/libSystem.tbd"
grep -m1 'armv7' "$DEST/iPhoneOS10.3.sdk/usr/lib/libSystem.tbd"
echo "SDK ready at $DEST/iPhoneOS10.3.sdk"
