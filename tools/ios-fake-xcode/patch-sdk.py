#!/usr/bin/env python3
"""Restore symbols the trimmed theos SDK stubs omit (idempotent).

The theos SDK .tbd files drop some symbols that genuinely exist on-device:
- libc++abi: ___gxx_personality_sj0 (SjLj personality iOS/ARM C++ needs)
- libcompiler_rt (via libSystem re-export): ___divmodsi4, ___udivmodsi4

Without them Apple ld64 fails the link even though dyld would resolve
everything at runtime. Run against the SDK *copy* used for linking.
Usage: patch-sdk.py <SDKROOT>
"""
import re
import sys

PATCHES = {
    "usr/lib/libc++abi.tbd": ["___gxx_personality_sj0"],
    "usr/lib/system/libcompiler_rt.tbd": ["___divmodsi4", "___udivmodsi4"],
    # present on-device, trimmed from stubs:
    # - stret: THE armv7 ObjC runtime helper (used by prebuilt libObjectAL)
    # - vm_region: legacy Mach VM query used by librobovm-core's thread.c
    #   (re-exported to the link via libSystem like the rest of libsystem_kernel)
    "usr/lib/libobjc.tbd": ["_objc_msgSend_stret"],
    "usr/lib/system/libsystem_kernel.tbd": ["_vm_region"],
}


def present(src, sym):
    # word match: plain substring lies (_vm_region vs _mach_vm_region)
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(sym) + r"(?![A-Za-z0-9_])", src) is not None


def add_symbols(path, symbols):
    src = open(path).read()
    missing = [s for s in symbols if not present(src, s)]
    if not missing:
        print(f"{path}: already complete")
        return
    # find the first `symbols:` flow list and insert before its closing ]
    m = re.search(r"symbols:\s*\[", src)
    assert m, f"no symbols list in {path}"
    i = m.end()
    depth = 1
    instr = False
    while depth > 0:
        c = src[i]
        if c == '"' and not instr:
            instr = True
        elif c == '"' and instr:
            instr = False
        elif not instr:
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
        i += 1
    close = i - 1
    # original list may or may not end with a trailing comma; separator first
    # (previous version appended "sym," which glued onto a comma-less tail)
    prev = src[:close].rstrip()
    sep = "" if prev.endswith(",") else ","
    ins = sep + ",".join(missing)
    src = src[:close] + ins + src[close:]
    open(path, "w").write(src)
    print(f"{path}: added {missing}")


def main(root):
    for rel, syms in PATCHES.items():
        add_symbols(f"{root}/{rel}", syms)


if __name__ == "__main__":
    main(sys.argv[1])
