"""Enforce conventional commit messages.

Accepted subject: <type>[(scope)]: <description>
Allowed types: feat, fix, docs, chore, refactor, test, build, ci, perf.
Merge and revert commits pass through untouched.
"""

import re
import subprocess
import sys

TYPES = ("feat", "fix", "docs", "chore", "refactor", "test", "build", "ci", "perf")
SUBJECT_RE = re.compile(rf"^({'|'.join(TYPES)})(\([a-z0-9_-]+\))?: .{{1,100}}$")
EMOJI_RE = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\u2b00-\u2bff\ufe0f]")


def message_path():
    if len(sys.argv) > 1:
        return sys.argv[1]
    root = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, check=True)
    return root.stdout.decode("utf-8").strip() + "/COMMIT_EDITMSG"


def main():
    with open(message_path(), encoding="utf-8") as handle:
        lines = [line for line in handle.read().splitlines() if not line.startswith("#")]
    text = "\n".join(lines).strip()
    if not text:
        print("Empty commit message.")
        return 1
    subject = text.splitlines()[0]
    if subject.startswith("Merge ") or subject.startswith("Revert "):
        return 0
    if EMOJI_RE.search(subject):
        print("Commit subject must not contain emoji.")
        return 1
    if not SUBJECT_RE.match(subject):
        print(f"Rejected subject: {subject}")
        print("Expected: <type>[(scope)]: <description>")
        print("Types: " + ", ".join(TYPES))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
