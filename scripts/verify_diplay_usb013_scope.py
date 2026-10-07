#!/usr/bin/env python3
"""Verify the USB investigation build has no changes to pinned upstream source."""
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1])
base = "6fb0fa4a09e77a84a437da5159147a6f6141ed61"

def git(*args):
    return subprocess.check_output(["git", "-C", str(root), *args])

assert git("rev-parse", "HEAD").decode().strip() == base
files = git("ls-tree", "-r", "--name-only", base).decode().splitlines()
for path in files:
    candidate = root / path
    assert candidate.is_file() and candidate.read_bytes() == git("show", f"{base}:{path}"), path
assert not git("ls-files", "--others", "--exclude-standard").strip()
print(f"PASS: all {len(files)} pinned upstream files are byte-identical; production source changes = 0")
print("Baseline: " + base)
