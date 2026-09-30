# UnleashedRecomp FMV Implementation Case Study

## Summary
This document analyzes the FMV (Full Motion Video) rendering approach utilized in the `UnleashedRecomp` (Xbox 360) static recompilation project, evaluating its viability as a model for the `shadow-the-hedgehog-recomp` (PS2) `sceMpeg` stubs.

## Architecture Analysis
The primary question driving this research was: *How did UnleashedRecomp intercept video rendering without external decoder libraries?*

Our investigation of the UnleashedRecomp repository revealed the following:
- **No External Libraries:** A codebase-wide search found no external libraries: third-party decoders like `FFmpeg`, `libmpeg2`, or Windows Media Foundation (`mfplat`) are not referenced.
- **Software Decoding via Transpilation:** Unlike the PS2, the Xbox 360 does not rely on a dedicated hardware chip like the IPU for video playback. The original *Sonic Unleashed* engine includes a software-based CRIWARE Sofdec decoder compiled directly into the `.xex` executable. 
- **Transpiled Decoder:** Because the Sofdec decoder consists of standard CPU math and lookup tables, the static recompilation pipeline translates it into C++ directly. The video decodes itself on the PC CPU natively, identically to how it ran on the Xbox 360 processor.
- **Mid-Asm Hooks:** The only manual hooks needed by the UnleashedRecomp team were purely aesthetic `MovieRendererMidAsmHook` patches located in `gpu/video.cpp` to map the decoded video frames to widescreen GPU quads/shaders (`movie_ps.hlsl`).

## Synthesis & Recommendations

The "UnleashedRecomp" strategy functions via direct software decoding because they decompiled a software-driven decoder. **This approach cannot be translated 1-to-1 to the PS2 architecture.**

1. **The Hardware Bottleneck:** Shadow the Hedgehog (`SLUS_212.61`) delegates video decoding to the PS2's fixed-function IPU silicon via the proprietary `sceMpeg` library. We cannot decompile a silicon chip into C++.
2. **Path Forward:** To achieve FMV rendering in our PS2 recompilation, we cannot rely on the generated C++ `sub_*.cpp` files to decode the video. We must implement a custom PC-native video decoder hook (e.g., using `FFmpeg`) inside `ps2xRuntime` that intercepts `sceMpegDemuxPss` calls, decodes the `.PSS` movie assets from `assets`, and pushes those frames directly to OpenGL/Raylib textures.

UnleashedRecomp got FMV "for free" thanks to its host architecture. We will have to build a native video player embedded in our HLE runtime.
