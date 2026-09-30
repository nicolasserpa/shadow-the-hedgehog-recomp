"""Generate register_functions.cpp from the recompiled function header.

Scans recomp/src/ps2_recompiled_functions.h for function symbols
and emits chunked registerAllFunctions_* registration calls.

Usage: python src/generate_register.py
Paths resolve relative to this script. The output lands in recomp/src/,
where src/CMakeLists.txt expects it.
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
HEADER_PATH = BASE_DIR.parent / "recomp" / "src" / "ps2_recompiled_functions.h"
OUT_PATH = BASE_DIR.parent / "recomp" / "src" / "register_functions.cpp"


def main():
    try:
        with open(HEADER_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as exc:
        print(f"Error opening header: {exc}")
        return 1

    pattern = re.compile(r"void\s+([a-zA-Z0-9_]+_0x([a-fA-F0-9]+))\s*\(")
    matches = pattern.findall(content)

    registered = []
    seen = set()
    for name, addr_hex in matches:
        address = int(str(addr_hex), base=16)
        if address not in seen:
            registered.append((addr_hex, name))
            seen.add(address)

    # Add the manual stub discovered missing dynamically
    if 0x66D5C0 not in seen:
        registered.append(("66d5c0", "sub_0066D5C0_0x66d5c0"))

    chunk_size = 4000
    chunks = [registered[i : i + chunk_size] for i in range(0, len(registered), chunk_size)]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("#include <cstdint>\n")
        f.write('#include "../../tools/PS2Recomp/ps2xRuntime/include/ps2_runtime.h"\n')
        f.write('#include "ps2_recompiled_functions.h"\n')
        f.write("extern void sub_0066D5C0_0x66d5c0(uint8_t*, R5900Context*, PS2Runtime*);\n\n")

        for i, chunk in enumerate(chunks):
            f.write(f"void registerAllFunctions_{i}(PS2Runtime& runtime) {{\n")
            for addr_hex, name in chunk:
                f.write(f"    runtime.registerFunction(0x{addr_hex}, {name});\n")
            f.write("}\n\n")

        f.write("void registerAllFunctions(PS2Runtime& runtime) {\n")
        for i in range(len(chunks)):
            f.write(f"    registerAllFunctions_{i}(runtime);\n")
        f.write("}\n")

    print(f"Extraction complete. Mapped {len(registered)} entries across {len(chunks)} chunked functions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
