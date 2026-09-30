# Building Shadow the Hedgehog (SLUS-212.61)

State: migrated to **PS2Recomp `75d729c`** ("Feature/iop emulator", PR #244).

## Machine prerequisites

A C++ toolchain must be installed. Without it nothing below works:

- Visual Studio 2022 Build Tools with the
  "Desktop development with C++" workload (MSVC v143 x64/x86 + Windows 10/11 SDK)
- CMake 3.21+ (validated with 4.2.3)

Install via winget (PowerShell as administrator):

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
winget install --id Kitware.CMake
```

A local PS2Recomp checkout is expected at `tools/PS2Recomp`. The game dump
belongs in `assets/` (see [docs/DUMPING.md](docs/DUMPING.md)).

## 1. Build ps2_recomp (the tool)

Separate build from the game. Only `ps2_recomp` is needed:

```powershell
cd tools/PS2Recomp
cmake -S . -B out/build -G "Visual Studio 17 2022" -A x64 `
  -DPS2X_BUILD_RUNTIME=OFF `
  -DPS2X_BUILD_ANALYZER=OFF `
  -DPS2X_BUILD_TEST=OFF `
  -DPS2X_BUILD_STUDIO=OFF
cmake --build out/build --config Release --target ps2_recomp
```

Output: `tools/PS2Recomp/out/build/ps2xRecomp/Release/ps2_recomp.exe`

## 2. Generate the recompiled code

The config is `shadow.toml` at the repository root, with
`low_memory_mode = true` / `output_worker_threads = 1`
(PR #128) to hold memory down. Run from the repository root so the
relative `assets/` and `recomp/` paths resolve:

```powershell
./tools/PS2Recomp/out/build/ps2xRecomp/Release/ps2_recomp.exe ./shadow.toml
```

Expected output in `recomp/src/`:

- `register_functions.cpp` — function table (new in 75d729c)
- `ps2_recompiled_functions.h`
- `ps2_recompiled_stubs.h`
- 22,732 `sub_XXXXXXX_0xXXXXXX.cpp`

`register_functions.cpp` is mandatory. Without it the build does not even
configure (`src/CMakeLists.txt` fails with an explicit message).

## 3. Build the game

This step is long (22,732 TUs). Suggested:

```powershell
cmake -S src -B src/build -G "Visual Studio 17 2022" -A x64
cmake --build src/build --config Release --target ShadowRecomp
```

`-j` does not apply to the Visual Studio generator; parallelism comes from
"Build > Parallel" / `-m`. `/MP1` on the target keeps 1 process per `cl.exe`.

CMake presets are provided (`CMakePresets.json`): `windows-vs2022-x64`
and `windows-ninja`.

## 4. Run

`ShadowRecomp.exe` starts without arguments: the boot ELF is baked in via
`PS2X_DEFAULT_BOOT_ELF`. For a different ELF:

```powershell
./src/build/Release/ShadowRecomp.exe D:/path/to/SLUS_212.61
```

## Useful tunables (cmake cache, no file edits)

| Variable | Default | Purpose |
|---|---|---|
| `SHADOW_UNITY_BATCH_SIZE` | `8` | Lower = less memory, slower. If RAM overflows, drop to 4. |
| `SHADOW_RECOMP_OPT` | `/Od` | `/Od` holds off C1060. `/O2` makes the game much faster, only after a green build. |
| `PS2X_ENABLE_DEBUG_UI` | `ON` | `OFF` removes imgui/raylib and the debug panel. |
| `PS2X_ENABLE_AGRESSIVE_LOGS` | `OFF` | `ON` enables verbose logging. Heavy. |

## Known issues

- **C1060 (out of heap)**: was the blocker of the old build. Addressed with
  `/Od` + PCH + unity build. If it returns, drop `SHADOW_UNITY_BATCH_SIZE` to 4
  or close other programs.
- **C2471 / 4GB PDB**: fixed by removing `/Zi` and `/ZI` from all configs.
- **LNK2005 duplicate `getGameName`**: `getGameName` now exists in
  `ps2xRuntime/src/lib/games_database.cpp`. Do not define it in
  `src/shadow_stubs.cpp`.
- **LNK2019 `sub_0066D5C0_0x66d5c0`**: ps2_recomp does not emit this address.
  Kept as a stub in `shadow_stubs.cpp`.
- **Function not found at runtime**: "Warning: Function at address 0x... not
  found" = the output was not recompiled or `register_functions.cpp` is
  stale. Regenerate and rebuild.

## Obsolete generation files (out of the build)

`src/generate_register.py` and the old `src/register_functions.cpp` were the
hand-made function table of the previous runtime version. PS2Recomp
`75d729c` generates the table itself, so neither is used anymore.
Both are preserved in case a comparison is needed.
