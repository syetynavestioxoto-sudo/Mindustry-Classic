# iOS arm32 (iPad mini 1st gen) build notes

Target: iPad mini 1st gen — Apple A5, **armv7**, 512 MB RAM, iOS 8.x–9.3.5,
jailbroken. App: Mindustry Classic (Java 8, libGDX 1.9.8, GLES2).

## Why not macOS runners / Xcode

Sep 2026 GitHub runners ship macOS 14/15/26 with **Xcode 15/16+ only**.
Apple removed armv7 in Xcode 10 and the minimum deployment target is
iOS 12, so no macOS runner can emit armv7/iOS 8 code — not even via
RoboVM (its compiler shells out to the active Xcode's `xcrun`/`lipo`/
`codesign`; see `ToolchainUtil.java` in MobiVM/robovm).

The 32-bit link therefore runs on **ubuntu-22.04** with:

- `clang` (emits `Mach-O armv7 object`, verified via `file`)
- [cctools-port](https://github.com/tpoechtrager/cctools-port) (Apple `ld64`
  + `lipo`, built from source for `arm-apple-darwin11`)
- [apple-libtapi](https://github.com/tpoechtrager/apple-libtapi) (parses
  the `.tbd` stub libraries; the SDK only ships stubs, not dylibs)
- [theos/sdks](https://github.com/theos/sdks) `iPhoneOS10.3.sdk`
  (tapi-tbd-v2, still contains the armv7 slice; linked with
  `-ios_version_min 8.0` + `MinimumOSVersion 8.0`)
- Java side: Temurin JDK 8 + Gradle 4.10.2 (period-correct for Classic).

## Linux patches (`fix_dispatch.py`)

Old ld64 uses Grand Central Dispatch APIs that modern Linux
swift-corelibs-libdispatch removed:

- `dispatch_apply(n, DISPATCH_APPLY_AUTO, ^(size_t i){...})` → serial
  `for` loop (linker host parallelism is optional). 7 sites across
  `order.cpp`, `code_dedup.cpp`, `InputFiles.cpp`, `OutputFile.cpp`,
  `Resolver.cpp`, `libcodedirectory.c`.
- `OutputFile::buildLINKEDITContent` GCD phase barriers
  (`dispatch_group_async`/`dispatch_group_wait`) → serial calls in the
  same dependency order (phase 1 → check → phase 2 → phase 3 → check).
- `DISPATCH_QUEUE_SERIAL` → `NULL` (serial is the default),
  `DISPATCH_QUEUE_PRIORITY_*` → default global queue.

## Artifacts (CI: `ios-arm32` workflow)

- `classic-jars`: `core`/`kryonet`/`server` jars built with JDK 8
  (the `html`/GWT module is dropped — its Gradle plugin only ever
  existed on the dead jcenter; same for the Android module/SDK).
- `classic-ios-armv7`: `hello` (console) + `Classic8` (minimal UIKit
  shell, iOS 8 APIs only) as **armv7 Mach-O**, plus
  `Classic8-armv7-unsigned.ipa` skeleton (`Payload/Classic8.app`
  with `MinimumOSVersion 8.0`, `armv7` + `opengles-2`).

## Install on the jailbroken iPad

The IPA is **unsigned** (no Apple codesign on Linux). Either:

1. Install [AppSync Unified](https://cydia.akemi.ai/) and install the
   IPA with Filza / `ideviceinstaller`, or
2. pseudo-sign on device: `ldid -S Classic8` (from Cydia), then
   `uicache` / respring.

`main.m` deliberately avoids ObjC struct returns (`-[UIScreen bounds]`
→ `_objc_msgSend_stret`), because the trimmed theos stubs don't export
that helper. Full game glue must either avoid struct-return ObjC calls
or link against complete Xcode `.tbd` files.

## Next step: the game itself

`Classic8` is a scaffold proving the Linux→armv7→IPA pipeline. Running
Classic needs, in this order:

1. JDK 8 for armv7 Darwin as a dylib (`libjvm`) — OpenJDK 8u `zero` or
   `client` (JIT works: jailbreak disables `cs_enforcement`, so
   `PROT_EXEC` mappings are allowed), installed to `/opt/jre` via `.deb`.
2. A loader (`dlopen` + `JNI_CreateJavaVM` + `CallStaticVoidMethod`)
   replacing `main.m`'s label with the game view.
3. JNI EAGL/GLES2 glue for libGDX 1.9.8 (its iOS backend is RoboVM-only;
   rewrite against the `gdx-backend-robovm` 1.9.8 sources as reference —
   all iOS 8-era APIs).
