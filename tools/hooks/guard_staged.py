"""Reject staged proprietary game assets and oversized blobs.

Game asset policy: the repository carries no game dumps, disc images,
executables, media streams or save data. Contributors provide
their own legally acquired copy locally (see docs/DUMPING.md).
"""

import subprocess

MAX_BYTES = 2_000_000

BANNED_EXTENSIONS = {
    ".iso",
    ".bin",
    ".cue",
    ".img",
    ".mdf",
    ".nrg",
    ".cso",
    ".elf",
    ".irx",
    ".iop",
    ".pss",
    ".pvs",
    ".m2v",
    ".mpg",
    ".mpeg",
    ".str",
    ".xa",
    ".adx",
    ".afs",
    ".ahx",
    ".acb",
    ".awb",
    ".hca",
    ".vag",
    ".ss2",
    ".mib",
    ".rws",
    ".dff",
    ".txd",
    ".col",
    ".ipl",
    ".p3d",
    ".pak",
    ".arc",
    ".ar",
    ".arl",
    ".psu",
    ".ps2",
    ".max",
    ".cbs",
    ".xps",
}

BANNED_PREFIXES = ("SLUS_", "SLES_", "SLPM_", "SCUS_", "SCES_")
BANNED_NAMES = {"SYSTEM.CNF"}


def staged_paths():
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACM"],
        capture_output=True,
        check=True,
    )
    return [p for p in out.stdout.decode("utf-8").split("\0") if p]


def staged_size(path):
    out = subprocess.run(
        ["git", "cat-file", "-s", f":0:{path}"],
        capture_output=True,
        check=True,
    )
    return int(out.stdout.decode("utf-8").strip())


def main():
    violations = []
    for path in staged_paths():
        name = path.rsplit("/", 1)[-1]
        ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
        upper = name.upper()
        if ext in BANNED_EXTENSIONS:
            violations.append(f"{path}: banned asset extension {ext}")
            continue
        if upper.startswith(BANNED_PREFIXES) or upper in BANNED_NAMES:
            violations.append(f"{path}: banned disc artifact name")
            continue
        if staged_size(path) > MAX_BYTES:
            violations.append(f"{path}: exceeds {MAX_BYTES} bytes")
    if violations:
        print("Proprietary asset guard blocked this operation:")
        for item in violations:
            print(f"  - {item}")
        print("Keep game dumps local. See docs/DUMPING.md.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
