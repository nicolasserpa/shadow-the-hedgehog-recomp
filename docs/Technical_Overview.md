# Technical Overview: Shadow the Hedgehog (PS2) Recompilation Architecture

## 1. Overview
This document outlines the architectural handling of executable logging and intro/FMV rendering within the *Shadow the Hedgehog (PS2)* static recompilation project. The project translates MIPS/VU binaries into native C++ while offloading hardware-specific subsystems to `ps2xRuntime`, a High-Level Emulation (HLE) abstraction layer.

## 2. Executable Logging Architecture
The original PS2 executable contains numerous logging calls (utilizing standard C library functions like `printf`, `sprintf`).
- **Interception via Config:** The transpiler is configured (`shadow.toml`) to explicitly stub these functions out. Instead of decompiling them into `sub_*.cpp`, the transpiler replaces calls to `printf` with hooks into `ps2xRuntime`.
- **Runtime Handling:** In `ps2xRuntime/src/lib/stubs/ps2_stubs_libc.inl`, `printf` is mapped to a C++ interceptor (`void printf(uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime)`).
- **Log Throttling:** To prevent the PC terminal from being overwhelmed by the game's verbose inner loops, the runtime implements a hard cap constraint (`kMaxPrintfLogs = 200`), after which standard console output (`std::cout`) is suppressed.

## 3. Intro Rendering & Video Logic
PlayStation 2 relies heavily on the Image Processing Unit (IPU) and the `sceMpeg` library to decode and render Full Motion Video (FMV) intros like `.PSS` files.
- **Hardware Emulation:** The core IPU hardware is emulated via direct memory-mapped hooks. E.g., writes to registers like `REG_IPU_CTRL (0x10002010)` and `REG_IPU_CMD` are intercepted by the runtime (`sceIpuInit`, `sceIpuRestartDMA`) and passed to host PC multimedia handlers.
- **MPEG Subsystem:** `sceMpegCreate`, `sceMpegDemuxPss`, and block-streaming functions are hooked natively inside `ps2xRuntime/src/lib/stubs/ps2_stubs_misc.inl`. The transpiler completely bypasses the original GS/VU1 decoding algorithms in favor of native PC video decoding, bridging PS2 VRAM buffers directly to standard DirectX/OpenGL textures.

## 4. Result
The recompilation offloads the complexity of translating raw IO and PS2 macroblock decoders directly to `ps2xRuntime`. By isolating Standard Library outputs and IPU registers via targeted HLE stubs, the transpiled C++ (`entry_*.cpp`) focuses strictly on game logic and rendering state, resulting in a cleaner, more performant native executable.
