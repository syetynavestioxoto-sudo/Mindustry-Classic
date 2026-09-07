"""Serialize Grand Central Dispatch parallel loops for old Apple ld64.

cctools-port ld64 (v956.6, Xcode 11 era) uses
    dispatch_apply(n, DISPATCH_APPLY_AUTO, ^(size_t i) { ... });
in 6 places. Modern Linux libdispatch removed DISPATCH_APPLY_AUTO and
modern clang rejects the block/lambda capture mix in those bodies.

For a linker host tool, parallelism is an optimization, not a
requirement: rewrite each call as a serial for-loop with a
comment/string-aware brace matcher.
"""
import re

FILES = [
    "cctools/ld64/src/ld/passes/order.cpp",
    "cctools/ld64/src/ld/passes/code_dedup.cpp",
    "cctools/ld64/src/ld/InputFiles.cpp",
    "cctools/ld64/src/ld/OutputFile.cpp",
    "cctools/ld64/src/ld/Resolver.cpp",
    "cctools/ld64/src/ld/libcodedirectory.c",
]

# Symbols Apple removed from modern libdispatch (Linux swift-corelibs).
# Serial is the default attr (NULL); QoS priorities collapse to the
# default global queue (0 = unspecified). This is a build host tool,
# scheduling hints don't matter.
QOS_COMPAT = {
    "DISPATCH_QUEUE_SERIAL": "NULL",
    "DISPATCH_QUEUE_PRIORITY_HIGH": "0",
    "DISPATCH_QUEUE_PRIORITY_DEFAULT": "0",
    "DISPATCH_QUEUE_PRIORITY_LOW": "0",
    "DISPATCH_QUEUE_PRIORITY_BACKGROUND": "0",
}

PAT = re.compile(
    r"dispatch_apply\s*\((.*),\s*DISPATCH_APPLY_AUTO\s*,\s*\^\(size_t\s+(\w+)\)\s*\{"
)


def find_matching_close(src, start):
    """start = index just after the opening '{'. Returns index of matching '}'."""
    i = start
    depth = 1
    instr = inch = False
    inlc = inbc = False
    esc = False
    n = len(src)
    while i < n and depth > 0:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if inlc:
            if c == "\n":
                inlc = False
        elif inbc:
            if c == "*" and nxt == "/":
                inbc = False
                i += 1
        elif instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        elif inch:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == "'":
                inch = False
        else:
            if c == "/" and nxt == "/":
                inlc = True
                i += 1
            elif c == "/" and nxt == "*":
                inbc = True
                i += 1
            elif c == '"':
                instr = True
            elif c == "'":
                inch = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
        i += 1
    assert depth == 0, "unbalanced braces"
    return i - 1


def main(root="."):
    total = 0
    for rel in FILES:
        path = f"{root}/{rel}"
        src = open(path).read()
        out = []
        pos = 0
        count = 0
        for m in PAT.finditer(src):
            expr, idx = m.group(1), m.group(2)
            close = find_matching_close(src, m.end())
            assert src[close + 1:close + 3] == ");", (
                f"expected ');' in {rel}, got {src[close + 1:close + 11]!r}"
            )
            body = src[m.end():close]
            out.append(src[pos:m.start()])
            out.append(
                f"for (size_t {idx} = 0; {idx} < ({expr}); ++{idx}) {{{body}}}"
                f" /* serialized from dispatch_apply for Linux */"
            )
            pos = close + 3
            count += 1
        out.append(src[pos:])
        patched = "".join(out)
        # compat shims for symbols removed from modern libdispatch
        for old, new in QOS_COMPAT.items():
            if old in patched:
                patched = patched.replace(old, new)
                count += 1
        open(path, "w").write(patched)
        print(f"{rel}: patched {count}")
        total += count
    print(f"total patched: {total}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else ".")
