# Dumping Guide

This project ships no game data. You must dump your own legally acquired
copy of *Shadow the Hedgehog* for PlayStation 2 (US release, `SLUS_212.61`)
and place the files under `assets/`. That directory is ignored by git and
is never uploaded.

## Required files

| File | Location | Purpose |
|---|---|---|
| `SLUS_212.61` | `assets/` | Game ELF, boot target and recompiler input |
| `SYSTEM.CNF` | `assets/` | Disc system file, boot metadata |
| `*.iso` (optional) | `assets/` | Full disc image, kept for reference |

The build only reads `assets/SLUS_212.61` (see `shadow.toml` and
`src/CMakeLists.txt`). The ELF boots by default; any other ELF can be
passed as `argv[1]` to `ShadowRecomp.exe`.

## Dumping the disc on Windows

1. Connect a drive able to read the original disc.
2. Create a byte-exact image with a dumping tool (for example ImgBurn in
   Read mode). Do not modify, patch or compress the result.
3. Extract `SLUS_212.61` and `SYSTEM.CNF` from the image root into `assets/`.
4. Verify the ELF size is 9,411,868 bytes before building.

## Rules

- Never commit anything under `assets/`. The asset guard hook and CI reject
  disc images, executables, media streams and saves.
- Never distribute dumped files. Link to this guide instead.
