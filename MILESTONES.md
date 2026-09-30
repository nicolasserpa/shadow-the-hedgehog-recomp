# Project Milestones — Shadow the Hedgehog (PS2 Recompilation)

Runtime execution and validation tracking for the post-recompilation layer.

- [x] **M1: Static compilation and linking**
  - **Criterion:** Produce the `ShadowRecomp.exe` binary linking the 1,589 objects emitted by `ps2recomp` with the static `ps2xRuntime` library.
  - **Status:** Done (202 MB, build 29/09/2026, 22,732 TUs).

- [x] **M2: Bootloader init (EE / RDRAM)**
  - **Criterion:** The executable initializes the virtual RDRAM (32 MB), starts the thread scheduler (EeScheduler) and opens the base window without an immediate segfault abort.
  - **Status:** Done (boot 0x100008, aliases 0x100fcc and 0x5f57d0, 640x448 window stable for 60s+).

- [ ] **M3: Video bypass (IPU / MPEG-2)**
  - **Criterion:** Intercept IPU/MPEG calls (Sega/Sonic Team logos), apply the `SkipFmv_CompleteIpuAndMpeg` stub (with CIS + CIM flags on the DMAC) and advance the pointer to the game loop without an infinite loop.
  - **Status:** In progress: stub implemented in `ps2xRuntime/src/lib/Kernel/Stubs/IPU.cpp`, verification pending.

- [ ] **M4: Menus and 2D interface (RenderWare / GS)**
  - **Criterion:** Intercept 2D primitives and GIF packets sent to the Graphics Synthesizer, rendering the title screen ("Press Start") and the option menus via Raylib.
  - **Status:** Planned.

- [ ] **M5: Controller input (DualShock 2 via Raylib)**
  - **Criterion:** `PadPollVBlank` routine processing polling on every V-Blank with a corrected active-low map and analog normalization, allowing menu navigation.
  - **Status:** Deadzone 0.15 applied in `ps2_pad.cpp` and `Pad.cpp`. libpad map validated.

- [ ] **M6: In-game 3D gameplay (Westopolis)**
  - **Criterion:** Stage file loading via local VFS (cdrom/host), geometry and physics microcode execution on the Vector Units (VU0/VU1) and 3D scene rendering.
  - **Status:** Blocked by M4 and M5.

- [ ] **M7: Polish and audio (SPU2 / stability)**
  - **Criterion:** Emulation/HLE of the SPU2 sound chip channels (synced BGM and SFX), corrected physics and a stable locked 60 FPS.
  - **Status:** Future.
