# Fake Xcode for RoboVM-on-Linux (jailbreak armv7 builds)

RoboVM 2.3.0 was written for macOS + Xcode, but every Xcode interaction
it needs for a *device release build* is shimable on Linux:

| Need | Real thing | This tree |
|---|---|---|
| `xcode-select --print-path` | Xcode path | `bin/xcode-select` → `$FAKEXCODE` |
| `xcrun -sdk <sdk> -f <tool>` | tool lookup | `bin/xcrun` maps to cctools/host tools |
| iOS link (`clang++` driver) | Apple clang + ld64 | `bin/clang-ios` translates driver flags to our Apple `ld64` (cctools-port) |
| `lipo`/`nm`/`otool`/`strip`/`ar`/`codesign_allocate` | cctools | cctools-port build (`arm-apple-darwin11-*`) |
| iOS SDK | `Xcode/.../SDKs` | theos `iPhoneOS10.3.sdk` (tbd-v2, has armv7), fetched at build time |
| `SDKSettings.plist` + platform `Info.plist` | inside Xcode/SDK | shipped with theos SDK + `platform-Info.plist` here |
| `dsymutil` | debug symbols | no-op shim (jailbreak release needs no dSYM) |
| `plutil` | plist conversion | no-op shim (iOS reads XML plists fine) |
| `pngcrush` | PNG optimization | skipped via `skipPngCrush` in `robovm.xml`; shim copies as fallback |
| `ibtool`/`actool` | storyboards/asset catalogs | hard-fail shims — Classic's `Assets.xcassets` was removed from `ios/data` for this reason (icons become default; acceptable for jailbreak) |
| `codesign`/`security`/provisioning | App Store signing | never reached: `iosSkipSigning = true` in `ios/build.gradle` (RoboVM prints "Skipping code signing...") |
| `PackageApplication` | IPA packaging | not used: build with `robovmInstall`, zip `Payload/` manually |
| `ios-sim`/`simlauncher`/libimobiledevice | run on simulator/device | not used: install the IPA over SSH/Filza/AppSync |

## Layout

- `bin/` — shims (must be on `PATH`, `FAKEXCODE` env must point here' parent)
- `Platforms/iPhoneOS.platform/Info.plist` — platform stub (SDK discovery)
- `Platforms/iPhoneOS.platform/Developer/SDKs/` — populated by `fetch-sdk.sh`
- `Toolchains/` — empty, satisfies Xcode path validation
- `version.plist` — fake Xcode 9.4.1 version (fallbacks exist, but be explicit)

## Build inside the container (`Containerfile`)

See `Containerfile`. It produces an image with JDK 8 + clang + cctools +
SDK + this tree, then runs:

```
./gradlew --no-daemon :ios:robovmInstall -Probovm.archs=thumbv7
```

then `package-ipa.sh` zips `build/robovm/*.app` into an unsigned IPA.
