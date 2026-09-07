#!/bin/sh
# Full local game build inside the robovm-ios container:
#   podman run --rm -v $PWD:/src -v <sdk>:/sdk:ro \
#     -v game-gradle-home:/gradle-home -v robovm-m2:/root/.m2 \
#     localhost/robovm-ios:latest bash /src/tools/ios-fake-xcode/build-game.sh
# Produces out/Mindustry-classic-ios8-armv7-unsigned.ipa
set -e
export FAKEXCODE=/opt/fakexcode DEVELOPER_DIR=/opt/fakexcode
export PATH=/opt/fakexcode/bin:$PATH
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export GRADLE_USER_HOME="${GRADLE_USER_HOME:-/gradle-home}"
export CLANG_IOS_LOG=/src/ios/build/clang-ios.log

SDKDEST=/opt/fakexcode/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs
mkdir -p "$SDKDEST"
if [ ! -d "$SDKDEST/iPhoneOS10.3.sdk" ]; then
    cp -r /sdk "$SDKDEST/iPhoneOS10.3.sdk"
fi
python3 /opt/fakexcode/patch-sdk.py "$SDKDEST/iPhoneOS10.3.sdk"

cd /src
./gradlew --no-daemon :ios:build :ios:robovmInstall -Probovm.archs=thumbv7

# Package the unsigned .app dir into an IPA (jailbreak install).
mkdir -p out/Payload
rm -rf out/Payload/Mindustry.app
cp -r ios/build/robovm out/Payload/Mindustry.app
rm -f out/Mindustry-classic-ios8-armv7-unsigned.ipa
(cd out && python3 -c "
import os, zipfile
with zipfile.ZipFile('Mindustry-classic-ios8-armv7-unsigned.ipa', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for dp, dn, fn in os.walk('Payload'):
        for f in sorted(dn + fn):
            p = os.path.join(dp, f)
            if os.path.isdir(p):
                z.writestr(p + '/', b'')
            else:
                z.write(p, p)
")
ls -la out/Mindustry-classic-ios8-armv7-unsigned.ipa
