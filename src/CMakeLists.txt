cmake_minimum_required(VERSION 3.21)
# MSVC linker (link.exe) instead of lld-link.
# lld-link (clang 23 default) fails the final link with "duplicate symbol:
# ShowCursor": raylib exports undecorated C names that collide with Win32
# (ShowCursor, GetClipboardText, SetClipboardText). link.exe resolves by
# archive order, as the MSVC build already did. Must come before
# project() so CMake generates the correct link rule.
set(CMAKE_LINKER_TYPE MSVC)
project(ShadowTheHedgehogRecomp LANGUAGES C CXX)

# ===========================================================================
#  Shadow the Hedgehog (SLUS-212.61) - recompiled code build
#
#  PS2Recomp used: tools/PS2Recomp @ 75d729c ("Feature/iop emulator", #244)
#
#  The official PS2Recomp target (ps2EntryRunner) builds everything under
#  ps2xRuntime/src/runner/. We prefer our own target (ShadowRecomp)
#  to keep the 22,732 generated files in recomp/src and out of
#  the tool tree. The runner code (main.cpp) matches upstream.
# ===========================================================================

set(SHADOW_PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.." CACHE PATH "Project root")
set(PS2RECOMP_DIR       "${SHADOW_PROJECT_ROOT}/tools/PS2Recomp" CACHE PATH "PS2Recomp tree")
set(SHADOW_RECOMP_DIR   "${SHADOW_PROJECT_ROOT}/recomp/src" CACHE PATH "ps2_recomp output")
set(SHADOW_ELF          "${SHADOW_PROJECT_ROOT}/assets/SLUS_212.61" CACHE FILEPATH "Guest ELF (boot)")

if(NOT EXISTS "${PS2RECOMP_DIR}/ps2xRuntime/CMakeLists.txt")
    message(FATAL_ERROR "PS2Recomp not found at '${PS2RECOMP_DIR}'.")
endif()

# ---------------------------------------------------------------------------
#  Strip debug info from the PDB (MSVC).
#  22,732 TUs exceeded the 4GB PDB limit and killed the build with C2471.
#  Must happen BEFORE add_subdirectory so the tool inherits it.
# ---------------------------------------------------------------------------
if(MSVC)
    set(SHADOW_CONFIGS DEBUG RELWITHDEBINFO)
    foreach(cfg IN LISTS SHADOW_CONFIGS)
        string(REGEX REPLACE "/Z[iI]" "" CMAKE_CXX_FLAGS_${cfg} "${CMAKE_CXX_FLAGS_${cfg}}")
        string(REGEX REPLACE "/Z[iI]" "" CMAKE_C_FLAGS_${cfg} "${CMAKE_C_FLAGS_${cfg}}")
    endforeach()
endif()

# ---------------------------------------------------------------------------
#  PS2Recomp options. Plain cache entries (no FORCE), so the cmake command
#  line (-D...) can override them without the next configure wiping them.
# ---------------------------------------------------------------------------
set(PS2X_ENABLE_RUNTIME_LOGS ON CACHE BOOL "PS2 runtime log")
set(PS2X_ENABLE_AGRESSIVE_LOGS OFF CACHE BOOL "Verbose logs (heavy on 21k TUs)")
set(PS2X_ENABLE_IOP_RPC_TRACE ON CACHE BOOL "IOP RPC trace")
set(PS2X_ENABLE_DEBUG_UI ON CACHE BOOL "Desktop debug panel (imgui)")

# The runner boots from this ELF when argv[1] is not given.
if(EXISTS "${SHADOW_ELF}")
    set(PS2X_DEFAULT_BOOT_ELF "${SHADOW_ELF}" CACHE STRING "Default boot ELF")
else()
    message(WARNING "ELF '${SHADOW_ELF}' not found. Pass the path as argv[1] at runtime.")
endif()

# ---------------------------------------------------------------------------
#  Order matters: ps2_runtime links ps2_iop, so ps2xIOP comes first.
#  (Same order as the PS2Recomp root CMakeLists.)
# ---------------------------------------------------------------------------
add_subdirectory("${PS2RECOMP_DIR}/ps2xIOP"     ps2xIOP_build)
add_subdirectory("${PS2RECOMP_DIR}/ps2xRuntime" ps2xRuntime_build)

# The tool's ps2EntryRunner only serves to test the tool itself.
# Here the executable is ShadowRecomp.
set_target_properties(ps2EntryRunner PROPERTIES EXCLUDE_FROM_ALL TRUE)

# ---------------------------------------------------------------------------
#  raylib vs Win32 clash on x64: ShowCursor and CloseWindow.
#
#  raylib defines both as strong global symbols in rcore.c.obj
#  (rcore.c:722 and platforms/rcore_desktop_glfw.c:998). On x64 these names
#  get no decoration, and the MSVC import lib packs EVERY thunk of
#  a DLL into a single .obj: pulling any user32 function also
#  materializes ShowCursor/CloseWindow -> LNK2005 in ShadowRecomp.
#
#  /FORCE:MULTIPLE (used upstream in ps2EntryRunner) would silence the error,
#  but here it would be silently wrong: user32.lib comes BEFORE raylib.lib
#  in the link line, so the ps2_runtime CloseWindow() would resolve to the
#  Win32 API and close a random window. Hence the rename.
#
#  None of the 22,732 generated files in recomp include raylib.h or
#  windows.h, and the runtime only calls its own raylib CloseWindow()
#  (ps2_runtime.cpp:552 and :2469), which is what we want to keep.
# ---------------------------------------------------------------------------
if(TARGET raylib)
    target_compile_definitions(raylib PRIVATE
        ShowCursor=ShowCursor_raylib
        CloseWindow=CloseWindow_raylib
    )
    if(TARGET ps2_runtime)
        target_compile_definitions(ps2_runtime PRIVATE
            ShowCursor=ShowCursor_raylib
            CloseWindow=CloseWindow_raylib
        )
    endif()
endif()

# ---------------------------------------------------------------------------
#  No LTO/IPO under clang-cl + link.exe.
#
#  The tool's ReleaseMode.cmake enables INTERPROCEDURAL_OPTIMIZATION_RELEASE on
#  ps2_runtime and ps2EntryRunner. With Clang that becomes -flto=thin, and the
#  .obj files come out as LLVM bitcode ("BC") instead of COFF. lld-link would
#  accept them (it does LTO), but with CMAKE_LINKER_TYPE=MSVC link.exe rejects
#  the lib with LNK1136 "corrupt or invalid file" -- and every LNK2001 on
#  PS2Runtime methods (Store16, clearLLBit, handleTLB*, ...) follows from
#  that, not from truly missing symbols.
#
#  Disabled here instead of editing the PS2Recomp clone. Cost: only
#  inter-module optimization in the runtime; the game does not depend on it.
# ---------------------------------------------------------------------------
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    foreach(shadow_tgt IN ITEMS ps2_runtime ps2EntryRunner)
        if(TARGET ${shadow_tgt})
            set_target_properties(${shadow_tgt} PROPERTIES
                INTERPROCEDURAL_OPTIMIZATION FALSE
                INTERPROCEDURAL_OPTIMIZATION_RELEASE FALSE
            )
        endif()
    endforeach()
endif()

# ---------------------------------------------------------------------------
#  MSVC-only flags leaking under clang-cl.
#
#  PS2Recomp uses if(MSVC) to pick flags, and CMake also sets MSVC=1
#  for clang-cl (it only mimics the MSVC ABI, it does not accept the flags).
#  The tool's ReleaseMode.cmake (ps2xRuntime/cmake/ReleaseMode.cmake:22) passes
#  /Qspectre-, which clang-cl rejects with "no such file or directory",
#  killing the ps2_runtime build.
#
#  Removed here instead of editing the PS2Recomp clone. The flags below are
#  all pure-MSVC optimizations: clang-cl is -O0 by default and does no
#  Spectre mitigation, so nothing is lost.
# ---------------------------------------------------------------------------
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    foreach(shadow_tgt IN ITEMS ps2_runtime ps2_iop raylib imgui rlImGui)
        if(NOT TARGET ${shadow_tgt})
            continue()
        endif()
        get_target_property(shadow_opts ${shadow_tgt} COMPILE_OPTIONS)
        if(NOT shadow_opts)
            continue()
        endif()
        # Each list element is one flag. An element containing
        # "Qspectre" is the MSVC flag clang-cl rejects.
        set(shadow_kept "")
        foreach(shadow_opt IN LISTS shadow_opts)
            if(shadow_opt MATCHES "Qspectre")
                continue()
            endif()
            list(APPEND shadow_kept "${shadow_opt}")
        endforeach()
        set_target_properties(${shadow_tgt} PROPERTIES
            COMPILE_OPTIONS "${shadow_kept}"
        )
    endforeach()
endif()

# ---------------------------------------------------------------------------
#  ps2_recomp output. The new recompiler emits 3 files the build
#  needs: the function table and the two headers.
# ---------------------------------------------------------------------------
foreach(shadow_required IN ITEMS
        "${SHADOW_RECOMP_DIR}/register_functions.cpp"
        "${SHADOW_RECOMP_DIR}/ps2_recompiled_functions.h"
        "${SHADOW_RECOMP_DIR}/ps2_recompiled_stubs.h")
    if(NOT EXISTS "${shadow_required}")
        message(FATAL_ERROR
            "Missing '${shadow_required}'.\n"
            "Run ps2_recomp before configuring the build (the tool build is\n"
            "separate; see BUILDING.md):\n"
            "  \"${PS2RECOMP_DIR}/out/build/ps2xRecomp/Release/ps2_recomp.exe\" \"${SHADOW_PROJECT_ROOT}/shadow.toml\"")
    endif()
endforeach()

file(GLOB_RECURSE SHADOW_RECOMP_SRCS CONFIGURE_DEPENDS "${SHADOW_RECOMP_DIR}/*.cpp")
list(LENGTH SHADOW_RECOMP_SRCS SHADOW_RECOMP_SRC_COUNT)
if(SHADOW_RECOMP_SRC_COUNT LESS 100)
    message(FATAL_ERROR
        "Only found ${SHADOW_RECOMP_SRC_COUNT} .cpp in '${SHADOW_RECOMP_DIR}'.\n"
        "Expected ~22.7k. The ps2_recomp generation probably failed.")
endif()
message(STATUS "Shadow: ${SHADOW_RECOMP_SRC_COUNT} translation units from ps2_recomp")

# ---------------------------------------------------------------------------
#  Game executable
# ---------------------------------------------------------------------------
add_executable(ShadowRecomp
    ${SHADOW_RECOMP_SRCS}
    "${CMAKE_CURRENT_SOURCE_DIR}/shadow_stubs.cpp"
    "${PS2RECOMP_DIR}/ps2xRuntime/src/main.cpp"
)

# ffmpeg DLLs next to the exe (same staging as upstream ps2EntryRunner).
ps2x_stage_ffmpeg_runtime_dlls(ShadowRecomp)

target_include_directories(ShadowRecomp PRIVATE
    "${SHADOW_RECOMP_DIR}"
)

# ---------------------------------------------------------------------------
#  Compiler: clang-cl instead of pure MSVC
#
#  cl.exe dies with C1060 (out of heap) on the giant files emitted
#  by ps2_recomp: the largest is 1.8M lines in a single TU. clang-cl
#  handles the same file with far less memory, so the game target uses
#  it. MSVC stays installed and builds ps2_recomp.
#
#  CMAKE_CXX_COMPILER_ID, not the MSVC variable: with clang-cl CMake still
#  marks MSVC=1, and the flags below (/FS /bigobj /Zm1500 /MP1) would be
#  forwarded to clang.
# ---------------------------------------------------------------------------
if(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    set(SHADOW_CRITICAL_OPT "/Od" CACHE STRING "Optimization flag for the giant files")
    set(SHADOW_RUNTIME_OPT "/O2" CACHE STRING "Optimization for the PS2Recomp libs")
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    set(SHADOW_CRITICAL_OPT "-O0" CACHE STRING "Optimization flag for the giant files")
    set(SHADOW_RUNTIME_OPT "-O2" CACHE STRING "Optimization for the PS2Recomp libs")
    # The code emitted by ps2_recomp uses _mm_blendv_ps and _mm_extract_epi32,
    # which are SSE4.1. The x64 default is SSE2, and clang (unlike MSVC)
    # refuses the always_inline: "requires target feature 'sse4.1'". Already
    # verified that _mm_adds_epu8, _mm_srai_epi16 etc. are SSE/SSE2, so SSE4.1
    # suffices -- no AVX2 needed. The CPU is a Ryzen 5 5600X (Zen 3) with
    # SSE4.1. clang-cl ignores /arch:SSE4.2; -msse4.1 is the flag that works.
    target_compile_options(ShadowRecomp PRIVATE -msse4.1)
else()
    set(SHADOW_CRITICAL_OPT "" CACHE STRING "Optimization flag for the giant files")
    set(SHADOW_RUNTIME_OPT "" CACHE STRING "Optimization for the PS2Recomp libs")
endif()
message(STATUS "Shadow: compiler '${CMAKE_CXX_COMPILER_ID}', giant file(s) with '${SHADOW_CRITICAL_OPT}'")

# Unity build: 22.7k TUs become ~2.8k units. That is what keeps the build
# inside the memory budget after the PCH.
set(SHADOW_UNITY_BATCH_SIZE 8 CACHE STRING "TUs per unity file (lower = less memory)")
set_target_properties(ShadowRecomp PROPERTIES
    UNITY_BUILD ON
    UNITY_BUILD_BATCH_SIZE "${SHADOW_UNITY_BATCH_SIZE}"
    OUTPUT_NAME "ShadowRecomp"
)

# The new ps2_recomp merges "additional entry points" into the owning function.
# That produces giant functions: 7 files > 4 MB, 229 MB total, and the
# largest (register_functions.cpp) is 88 MB / an array of 1.97M entries. If
# they entered the unity build they would form a single ~100 MB file and
# cl.exe would die (C1060). They build standalone.
set(SHADOW_UNITY_MAX_FILE_MB 4 CACHE STRING "Files above this stay out of the unity build")
math(EXPR SHADOW_UNITY_MAX_FILE_BYTES "${SHADOW_UNITY_MAX_FILE_MB} * 1024 * 1024")

set(SHADOW_UNITY_EXCLUDED "")
foreach(shadow_src IN LISTS SHADOW_RECOMP_SRCS)
    file(SIZE "${shadow_src}" shadow_src_size)
    if(shadow_src_size GREATER SHADOW_UNITY_MAX_FILE_BYTES)
        list(APPEND SHADOW_UNITY_EXCLUDED "${shadow_src}")
    endif()
endforeach()

if(SHADOW_UNITY_EXCLUDED)
    list(LENGTH SHADOW_UNITY_EXCLUDED SHADOW_UNITY_EXCLUDED_COUNT)
    set_source_files_properties(${SHADOW_UNITY_EXCLUDED} PROPERTIES
        SKIP_UNITY_BUILD_INCLUSION TRUE
        COMPILE_OPTIONS "${SHADOW_CRITICAL_OPT}"
    )
    message(STATUS
        "Shadow: ${SHADOW_UNITY_EXCLUDED_COUNT} file(s) > ${SHADOW_UNITY_MAX_FILE_MB} MB "
        "outside the unity build, built standalone with '${SHADOW_CRITICAL_OPT}'")
    foreach(shadow_big IN LISTS SHADOW_UNITY_EXCLUDED)
        get_filename_component(shadow_big_name "${shadow_big}" NAME)
        file(SIZE "${shadow_big}" shadow_big_size)
        message(STATUS "  isolated: ${shadow_big_name} (${shadow_big_size} bytes)")
    endforeach()
endif()

# PCH with the heavy headers. Without it each of the 22,732 TUs reparses
# ps2_runtime.h and the 22,732-declaration header.
target_precompile_headers(ShadowRecomp PRIVATE
    "${PS2RECOMP_DIR}/ps2xRuntime/include/ps2_runtime_macros.h"
    "${PS2RECOMP_DIR}/ps2xRuntime/include/ps2_runtime.h"
    "${PS2RECOMP_DIR}/ps2xRuntime/include/ps2_syscalls.h"
    "${PS2RECOMP_DIR}/ps2xRuntime/include/ps2_stubs.h"
    "${SHADOW_RECOMP_DIR}/ps2_recompiled_functions.h"
    "${SHADOW_RECOMP_DIR}/ps2_recompiled_stubs.h"
)

# ps2_runtime exports include/ and ps2_iop; both arrive via PUBLIC.
target_link_libraries(ShadowRecomp PRIVATE ps2_runtime)

if(PS2X_ENABLE_DEBUG_UI)
    target_sources(ShadowRecomp PRIVATE
        "${PS2RECOMP_DIR}/ps2xRuntime/src/lib/ps2_debug_panel.cpp"
    )
    target_link_libraries(ShadowRecomp PRIVATE rlImGui imgui)
    target_compile_definitions(ShadowRecomp PRIVATE PS2X_ENABLE_DEBUG_UI=1)
endif()

# ---------------------------------------------------------------------------
#  Flags per compiler
#
#  Pure MSVC: /FS (PDB shared across parallel cl.exe), /bigobj (large
#  .obj sections), /Zm1500 (internal allocation limit), /MP1 (1 process per
#  cl.exe; parallelism comes from cmake --build -j) and /Od.
#
#  clang-cl: these MSVC flags don't apply, and it already compiles at -O0.
#  The PS2Recomp libs (ps2_runtime/ps2_iop) get -O2 so the game doesn't
#  run at debugger speed. CMAKE_BUILD_TYPE stays empty on purpose:
#  with "Release" the tool's ReleaseMode.cmake enables /GL + LTO, and linking
#  22.7k TUs with LTO is what blows the memory budget.
# ---------------------------------------------------------------------------
if(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    target_compile_options(ShadowRecomp PRIVATE /FS /bigobj /Zm1500 /MP1)
    if(SHADOW_RECOMP_OPT)
        separate_arguments(SHADOW_RECOMP_OPT_LIST UNIX_COMMAND "${SHADOW_RECOMP_OPT}")
        target_compile_options(ShadowRecomp PRIVATE ${SHADOW_RECOMP_OPT_LIST})
    endif()
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    if(SHADOW_RECOMP_OPT)
        separate_arguments(SHADOW_RECOMP_OPT_LIST UNIX_COMMAND "${SHADOW_RECOMP_OPT}")
        target_compile_options(ShadowRecomp PRIVATE ${SHADOW_RECOMP_OPT_LIST})
    endif()
    if(SHADOW_RUNTIME_OPT)
        separate_arguments(SHADOW_RUNTIME_OPT_LIST UNIX_COMMAND "${SHADOW_RUNTIME_OPT}")
        target_compile_options(ps2_runtime PRIVATE ${SHADOW_RUNTIME_OPT_LIST})
        target_compile_options(ps2_iop PRIVATE ${SHADOW_RUNTIME_OPT_LIST})
        # raylib/imgui/rlImGui come from FetchContent. With empty
        # CMAKE_BUILD_TYPE they would also sit at -O0, and the game window
        # would lose performance with no memory gain (a few small files).
        foreach(shadow_dep IN ITEMS raylib imgui rlImGui)
            if(TARGET ${shadow_dep})
                target_compile_options(${shadow_dep} PRIVATE ${SHADOW_RUNTIME_OPT_LIST})
            endif()
        endforeach()
    endif()
endif()

message(STATUS "Shadow: unity batch ${SHADOW_UNITY_BATCH_SIZE}, ELF ${SHADOW_ELF}")
