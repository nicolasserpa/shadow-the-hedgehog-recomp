// Shadow the Hedgehog (SLUS-212.61) specific stubs and overrides.
//
// PS2Recomp @ 75d729c: this file is part of the ShadowRecomp target.
//
// NOTE: do not define getGameName here. Since 75d729c it lives in
// ps2xRuntime/src/lib/games_database.cpp (inside ps2_runtime) and upstream
// treats a game outside the database as nullptr, falling back to the ELF
// filename for the title. The old version of this file defined getGameName
// and broke the link with LNK2005 (duplicate symbol).
//
// Per-game hacks (syscall, stub, address binding) go through the official
// ps2_game_overrides::AutoRegister mechanism instead of touching the
// runtime.

#include "ps2_runtime.h"
#include "ps2_recompiled_functions.h"
#include "ps2_runtime_macros.h"
#include "game_overrides.h"

namespace {

void applyShadowBootMidFunctionAlias(PS2Runtime &runtime) {
    runtime.registerFunction(0x100fbcu, sub_00100F60_0x100f60);
    runtime.registerFunction(0x100fccu, sub_00100F60_0x100f60);
    runtime.registerFunction(
        0x5f57d0u,
        [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
            (void)runtime;
            (void)rdram;
            SET_GPR_S32(ctx, 3, -1);
            SET_GPR_U64(ctx, 2, GPR_U64(ctx, 4));
            WRITE32(ADD32(GPR_U32(ctx, 4), 4), GPR_U32(ctx, 3));
            WRITE32(ADD32(GPR_U32(ctx, 4), 0), GPR_U32(ctx, 3));
            WRITE8(ADD32(GPR_U32(ctx, 4), 9), (uint8_t)0);
            WRITE8(ADD32(GPR_U32(ctx, 4), 8), (uint8_t)0);
            ctx->pc = GPR_U32(ctx, 31);
        });
}

// HLE of DPRINTF via DECI2 (sub_0010F1B8 -> wrapper 0x10EDE0).
//
// The game formats text into a 256-byte buffer (converting LF to CR),
// raises the busy flag *(0x0008315C) = 1 and spins in the 0x10F2D8 loop
// calling 0x10EDE0 = Deci2Call(4, sp) (sceDeci2Poll) until the flag clears.
// On real hardware the async send completion clears the flag; without a
// host DECI2 the runtime never completes and the game hangs with PC stuck
// at 0x0010F2D8.
//
// 0x10EDE0 has a single caller (the sub_0010F1B8 loop), so the override
// emulates "poll found send complete": it clears *(s0 + 0xC) of the caller,
// returns 0 (success) and resumes at 0x10F2E4, which exits the loop on the
// happy path (no error fallback).
void applyShadowDeci2PollCompletion(PS2Runtime &runtime) {
    runtime.registerFunction(
        0x10ede0u,
        [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
            WRITE32(ADD32(GPR_U32(ctx, 16), 12), GPR_U32(ctx, 0));
            SET_GPR_S32(ctx, 2, 0);
            ctx->pc = GPR_U32(ctx, 31);
        });
}

// HLE of sceSifGetReg (syscall 0x7a via wrapper 0x10DE70).
//
// The runtime dispatcher has no 0x79/0x7a/0x7b case and falls into a TODO
// that returns 0. The game hangs in SifInitRpc/SifInitCmd:
// - 0x110AB8: calls 0x10DE70 with a0=4 in a loop until (v0 & 0x20000).
// - 0x117148: calls 0x10DE70 with a0=4 and tests (v0 & 0x40000).
// - 0x110A64/0x116FF8: call with a0=0x80000000 and test beqz.
// The runtime already seeds reg 4 = 0x20000, but it never arrives without
// a route. The override reports IOP ready: reg 4 = 0x60000
// (0x20000|0x40000). Other regs return 0, same as the official stub.
void applyShadowSifGetRegReady(PS2Runtime &runtime) {
    runtime.registerFunction(
        0x10de70u,
        [](uint8_t *rdram, R5900Context *ctx, PS2Runtime *runtime) {
            (void)runtime;
            (void)rdram;
            const uint32_t reg = GPR_U32(ctx, 4);
            uint32_t value = 0u;
            if (reg == 0x4u) {
                value = 0x00020000u | 0x00040000u;
            }
            SET_GPR_U32(ctx, 2, value);
            ctx->pc = GPR_U32(ctx, 31);
        });
}

}  // namespace

PS2_REGISTER_GAME_OVERRIDE(
    "shadow-boot-alias",
    "SLUS_212.61",
    0x100008u,
    0u,
    applyShadowBootMidFunctionAlias);

PS2_REGISTER_GAME_OVERRIDE(
    "shadow-deci2-poll-complete",
    "SLUS_212.61",
    0x100008u,
    0u,
    applyShadowDeci2PollCompletion);

PS2_REGISTER_GAME_OVERRIDE(
    "shadow-sif-getreg-ready",
    "SLUS_212.61",
    0x100008u,
    0u,
    applyShadowSifGetRegReady);

// Active overrides for SLUS-212.61 in the current state:
// - shadow-boot-alias (boot mid-function alias).
// - shadow-deci2-poll-complete (DPRINTF HLE via DECI2, unsticks 0x10F2D8).
// - shadow-sif-getreg-ready (sceSifGetReg 0x7a HLE, unsticks 0x110AC0).
//
// sub_0066D5C0_0x66d5c0 was stubbed here when ps2_recomp did not generate
// that address yet. Current generation produces
// recomp/src/sub_0066D5C0_0x66d5c0.cpp with the recompiled
// implementation, and keeping both broke the link with LNK2005 (duplicate
// symbol) between unity_2766 and unity_2840.
//
// If a stub is needed again, the official mechanism is
// ps2_game_overrides::AutoRegister, not a direct definition here.
