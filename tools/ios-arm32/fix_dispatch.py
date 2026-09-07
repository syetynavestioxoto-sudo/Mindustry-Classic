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


LINKEDIT_SIG = "void OutputFile::buildLINKEDITContent(ld::Internal& state)"

LINKEDIT_SERIAL = """void OutputFile::buildLINKEDITContent(ld::Internal& state)
{
	// linux-serialized: GCD parallel dispatch replaced with serial calls
	const char* exceptionMsg = nullptr;

	// phase 1: build state.stabs and _importedAtoms, _exportedAtoms, _localAtoms
	try {
		this->synthesizeDebugNotes(state);	// needs state.section.atoms, updates: state.stabs
	}
	catch (const char* msg) {
		exceptionMsg = msg;
	}
	try {
		this->partitionSymbolTable(state);	// needs state.section.atoms, updates: _importedAtoms, _exportedAtoms, _localAtoms, `Atom::_outputSymbolIndex`
	}
	catch (const char* msg) {
		exceptionMsg = msg;
	}
	if ( exceptionMsg != nullptr )
		throw exceptionMsg;

	// phase 2: once stabs are built and atoms paritioned into symbol table slices, the symbol table indexes can be recorded
	assignSymbolIndexes(state);

	// phase 3: build linkedit parts that depend on results of phase 1
	if ( _hasDyldInfo || _hasSectionRelocations || _hasLocalRelocations || _hasExternalRelocations || _hasThreadedPageStarts ) {
		try {
			this->buildLinkEditOpcodes(state);	// needs state.section.atoms, `Atom::_outputSymbolIndex`, updates: _rebasingInfoAtom, _bindingInfoAtom, _weakBindingInfoAtom, _weakBindingInfoAtom, _sectionsRelocationsAtom
		}
		catch (const char* msg) {
			exceptionMsg = msg;
		}
	}
	else if ( _hasChainedFixups ) {
		try {
			this->buildChainedFixupInfo(state);  // needs state.section.atoms, updates: _chainedFixupSegments, _importedSymbolsCount, _chainedInfoAtom
		}
		catch (const char* msg) {
			exceptionMsg = msg;
		}
	}
	if ( _options.sharedRegionEligible() || _options.emitSharedRegionMarker() ) {
		this->makeSplitSegInfo(state);	 // needs state.section.atoms, updates: _splitSegInfoAtom
		_splitSegInfoAtom->encode();
	}
	if ( _exportInfoAtom != nullptr ) {
		try {
			_exportInfoAtom->encode(); 		// needs _exportedAtoms, updates: _exportInfoAtom
		} catch ( const char* msg ) {
			exceptionMsg = msg;
		}
	}
	try {
		_symbolTableAtom->encode();			// needs _importedAtoms, _exportedAtoms, _localAtoms, state.stabs, updates: _symbolTableAtom
		_indirectSymbolTableAtom->encode(); // needs state.section.atoms, `Atom::_outputSymbolIndex`, updates:  _indirectSymbolTableAtom
	}
	catch (const char* msg) {
		exceptionMsg = msg;
	}
	if ( _functionStartsAtom != nullptr ) {
		_functionStartsAtom->encode();	// needs state.section.atoms
	}
	if ( _dataInCodeAtom != nullptr ) {
		_dataInCodeAtom->encode();		// needs state.section.atoms
	}
	if ( _optimizationHintsAtom != nullptr ) {
		_optimizationHintsAtom->encode(); // needs state.section.atoms
	}

	if ( exceptionMsg != nullptr )
		throw exceptionMsg;
}
"""


def patch_linkedit(root):
    rel = "cctools/ld64/src/ld/OutputFile.cpp"
    path = f"{root}/{rel}"
    src = open(path).read()
    start = src.find(LINKEDIT_SIG)
    assert start != -1, "buildLINKEDITContent not found"
    brace = src.find("{", start)
    assert brace != -1
    close = find_matching_close(src, brace + 1)
    src = src[:start] + LINKEDIT_SERIAL + src[close + 1:]
    open(path, "w").write(src)
    print(f"{rel}: buildLINKEDITContent serialized")
    return 1


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
    total += patch_linkedit(root)
    print(f"total patched: {total}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else ".")
