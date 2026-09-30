# Shadow the Hedgehog (PS2) - PC Recompilation

Static recompilation of the PlayStation 2 release of *Shadow the Hedgehog*
(SLUS-212.61) into native x86_64 C++ linked against `ps2xRuntime`, which
provides high-level emulation (HLE) of the PS2 hardware abstraction layer.

## Game Assets
This repository contains no game assets. See [docs/DUMPING.md](docs/DUMPING.md).

## Status

| Milestone | State |
|---|---|
| M1: Static compilation and linking (`ShadowRecomp.exe`, 202 MB) | done |
| M2: Bootloader and RDRAM init (window 640x448, 60s+ stable) | done |
| M3: Video bypass (IPU/MPEG stub) | in progress |
| M4: 2D menus (RenderWare/GS via Raylib) | planned |
| M5: Controller input (DualShock 2 via Raylib) | in progress |
| M6: In-game 3D (Westopolis) | blocked by M4/M5 |
| M7: Audio (SPU2) and 60 FPS lock | planned |

Details in [MILESTONES.md](MILESTONES.md).

## Requirements

- CMake 3.21 or newer.
- Visual Studio 2022 Build Tools (MSVC v143) or clang-cl, with C++20 support.
- A local PS2Recomp checkout at `tools/PS2Recomp` (upstream commit `75d729c`).
- Python 3.10+ with `ruff`, `mypy`, `cpplint` for the hooks (`pip install -r requirements.txt`).
- Scoop packages on Windows: `lefthook`, `python` (`lefthook install` enables the git hooks).

## Build

```powershell
# 1. Build the recompiler tool
cmake -S tools/PS2Recomp -B tools/PS2Recomp/out/build -G "Visual Studio 17 2022" -A x64 `
  -DPS2X_BUILD_RUNTIME=OFF -DPS2X_BUILD_ANALYZER=OFF -DPS2X_BUILD_TEST=OFF -DPS2X_BUILD_STUDIO=OFF
cmake --build tools/PS2Recomp/out/build --config Release --target ps2_recomp

# 2. Recompile the game ELF (run from the repository root)
./tools/PS2Recomp/out/build/ps2xRecomp/Release/ps2_recomp.exe ./shadow.toml

# 3. Build the game
cmake -S src -B src/build -G "Visual Studio 17 2022" -A x64
cmake --build src/build --config Release --target ShadowRecomp
```

Full procedure, cache variables and known issues: [BUILDING.md](BUILDING.md).

## Layout

| Path | Content |
|---|---|
| `assets/` | Local user-provided dump (ignored by git) |
| `recomp/` | Generated C++ from `ps2_recomp` (ignored by git) |
| `src/` | Build files: `CMakeLists.txt`, `shadow_stubs.cpp`, dev scripts |
| `shadow.toml` | Recompiler configuration (stubs, skip, jump tables) |
| `symbols.csv` | Boot symbols |
| `tools/` | Python/PowerShell utilities and git hook scripts |
| `docs/` | Technical overview, dumping guide, case study |
| `tests/` | QA placeholder |

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) first. Generated files under
`recomp/` are never edited by hand; fixes go through `shadow.toml` stubs
or native HLE hooks in the runtime. Commits follow Conventional Commits
and are checked by lefthook (`ruff`, `mypy`, `cpplint`, asset guard).

## License

GPL-3.0. See [LICENSE](LICENSE).

## Credits

- `ps2xRecomp` / `ps2xRuntime` by ran-j ([PS2Recomp](https://github.com/ran-j/PS2Recomp)).
- Rendering and input via [raylib](https://www.raylib.com/), debug UI via imgui.
- Static-recompilation approach pioneered by [N64Recomp](https://github.com/N64Recomp/N64Recomp).
