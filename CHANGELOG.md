# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Static recompilation infrastructure setup for transpiling MIPS R5900/VU binaries to x86_64 C++.
- Successful Phase 1 extraction of the base ELF (`SLUS_212.61`) and assets.
- Explicit transpiler stubs in `shadow.toml` for standard C-library hooks (`printf`, `sprintf`, `malloc`, etc.) routing to native `ps2xRuntime` endpoints.
- Integration of internal High-Level Emulation (HLE) stubs for IPU and `sceMpeg` hardware decoding to bypass PS2-specific video routines in favor of PC-native rendering hooks.
- Documented `docs/Technical_Overview.md` detailing the architectural separation between static translation units and native runtime hooks.

### Known Issues
- The main execution loop cannot currently reach or render the intro FMV due to pending runtime hook validations and unmapped hardware stubs.
