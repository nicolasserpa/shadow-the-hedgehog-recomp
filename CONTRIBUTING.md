# Contributing Guidelines

Contributions target runtime hooks and optimizations. Transpiler output stays untouched.

## Core Architectural Policies

1. **Immutability of Transpiled Sources**
   Under no circumstances should manual edits be committed to the generated translation units located in `recomp/src/` (e.g., `sub_*.cpp` or `entry_*.cpp`). These files are the deterministic output of the transpiler pipeline. 
   Modifications required to resolve execution logic errors, bypass memory leaks, or optimize rendering MUST be implemented via runtime hooks, trampolines, or detours in the native execution space. Direct modification of transpiled sources will result in complete data loss upon the next decompilation cycle.
   
   **Note on Stubs and Hardware Calls:** If a new system C-library function (e.g., `printf`) or PS2 hardware library call (e.g., `sceMpeg`/`sceIpu`) is discovered during development, do not attempt to manually fix its transpiled output. Instead, add it to the `stubs` array in `shadow.toml` and implement the corresponding native HLE hook inside `ps2xRuntime`.

2. **Feature Branching Strategy**
   All contributions must follow a clear branching nomenclature. 
   - Feature integrations (e.g., modern resolutions, input wrappers): `feat/widescreen-wrapper`
   - Stability patches (e.g., crash resolutions, stutter fixes): `fix/camera-frametime`

3. **Issue Reporting**
   Bug reports must include:
   - A technical description of the failure (what ran, what happened).
   - Build logs (compiler and linker output) for the failing stage.
   - Runtime logs from the execution stage where the failure occurs.

## Submitting a Pull Request

1. Fork the repository and isolate your hook implementations.
2. Validate local compilation through the standard CMake pipeline (`cmake --build src/build`). The codebase must compile with zero linker errors.
3. Submit the Pull Request with a clear summary outlining the intercepted addresses and the operational goal of the detour.
4. Maintainers review the footprint before merging. 
