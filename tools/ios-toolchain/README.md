# Apple cctools (ld64/lipo/...) for Linux, able to emit armv7 iOS binaries.

Built from [cctools-port](https://github.com/tpoechtrager/cctools-port)
plus [apple-libtapi](https://github.com/tpoechtrager/apple-libtapi),
with `fix_dispatch.py` serializing the Grand Central Dispatch use that
modern Linux libdispatch removed (`dispatch_apply` → `for`,
`buildLINKEDITContent` phases → serial calls, removed constants shimmed).

## Critical build note

**Build cctools with `make -j1`.** Parallel make has missing dependencies
in this tree and *silently* relinks a corrupt `ld`: correct size, all-zero
content, exit code 0. Only `xxd`/`od` on a test link reveals it
(`file` just says `data`). Serial build is slow (~10 min on 4 cores) but
deterministic. Always smoke-test the result:

```
clang -target armv7-apple-ios -isysroot <SDK> -c hello.c -o hello.o
arm-apple-darwin11-ld -arch armv7 -ios_version_min 8.0 -no_uuid \
  -syslibroot <SDK> -o hello hello.o -lSystem
od -A x -t x1z hello | head -1   # must start with ce fa ed fe
```

## Files

- `Containerfile` — image definition (ubuntu:22.04 + clang + cctools).
- `fix_dispatch.py` — the Linux port patches (run before `configure`).
- `build-ldid.sh` — builds a Linux `ldid` (replaces RoboVM's macOS-only
  one for jailbreak pseudo-signing).
