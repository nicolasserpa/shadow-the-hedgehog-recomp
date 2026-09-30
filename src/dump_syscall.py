"""Dump the MIPS word at a target virtual address from a PS2 ELF.

Resolves the virtual address through the ELF program headers and
decodes a SYSCALL immediate when present.

Usage: python src/dump_syscall.py [elf_path] [vaddr_hex]
Defaults to assets/SLUS_212.61 at 0x100FCC.
"""

import struct
import sys
from pathlib import Path

DEFAULT_ELF = Path(__file__).resolve().parent.parent / "assets" / "SLUS_212.61"
DEFAULT_VADDR = 0x100FCC


def main():
    elf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ELF
    target_vaddr = int(sys.argv[2], 16) if len(sys.argv) > 2 else DEFAULT_VADDR

    with open(elf_path, "rb") as f:
        # Read ELF header to find Program Headers
        f.seek(0x1C)  # e_phoff
        phoff = struct.unpack("<I", f.read(4))[0]

        f.seek(0x2A)  # e_phentsize
        phentsize = struct.unpack("<H", f.read(2))[0]

        f.seek(0x2C)  # e_phnum
        phnum = struct.unpack("<H", f.read(2))[0]

        file_offset = -1

        for i in range(phnum):
            f.seek(phoff + i * phentsize)
            entry = struct.unpack("<IIIIIIII", f.read(32))
            p_type, p_offset, p_vaddr, p_memsz = entry[0], entry[1], entry[2], entry[5]

            if p_type == 1 and p_vaddr <= target_vaddr < p_vaddr + p_memsz:  # PT_LOAD
                file_offset = int(p_offset + (target_vaddr - p_vaddr))
                break

        if file_offset != -1:
            f.seek(file_offset)
            word = struct.unpack("<I", f.read(4))[0]
            # Syscall instruction is: code << 6 | 0x0C
            if (word & 0x3F) == 0x0C:
                syscall_code = (word >> 6) & 0xFFFFF
                print(
                    f"[DEBUG] Instruction at 0x{target_vaddr:X} is SYSCALL."
                    f" Immediate Code: 0x{syscall_code:X} ({syscall_code})"
                )

                # Peek at previous instructions to check whether $v1 (reg 3)
                # is loaded with the syscall ID.
                f.seek(file_offset - 16)
                print("[DEBUG] Previous instructions:")
                for _j in range(4):
                    prev_word = struct.unpack("<I", f.read(4))[0]
                    print(f"  - 0x{prev_word:08X}")
            else:
                print(
                    f"[DEBUG] Target address 0x{target_vaddr:X} does NOT contain"
                    f" a SYSCALL instruction. Word: 0x{word:08X}"
                )
        else:
            print("[DEBUG] Virtual address not mapped in ELF.")


if __name__ == "__main__":
    main()
