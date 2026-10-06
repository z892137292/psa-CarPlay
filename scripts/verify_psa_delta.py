#!/usr/bin/env python3
"""Verify the reconstructed 0.2.9 source against the actual 0.2.8 patch baseline."""
import pathlib
import sys

baseline, candidate = map(pathlib.Path, sys.argv[1:3])
protected_dirs = [
    "shared/src/main/java/com/shilapi/xcertplay/airplay",
    "shared/src/main/java/com/shilapi/xcertplay/mfi",
    "shared/src/main/java/com/shilapi/xcertplay/transport",
    "shared/src/main/java/com/shilapi/xcertplay/media",
]
protected_files = [
    "shared/src/main/java/com/shilapi/xcertplay/network/CarPlayBonjour.kt",
    "shared/src/main/java/com/shilapi/xcertplay/network/CarPlayVpnService.kt",
    "shared/src/main/java/com/shilapi/xcertplay/network/WifiP2pGroupManager.kt",
]
paths = set(protected_files)
for directory in protected_dirs:
    for root in (baseline, candidate):
        paths.update(str(p.relative_to(root)) for p in (root / directory).rglob("*") if p.is_file())
for relative in sorted(paths):
    old, new = baseline / relative, candidate / relative
    assert old.is_file() and new.is_file() and old.read_bytes() == new.read_bytes(), relative
changes = []
for file in sorted(candidate.rglob("*")):
    if not file.is_file() or ".git" in file.parts or "build" in file.parts or ".gradle" in file.parts:
        continue
    relative = file.relative_to(candidate)
    if str(relative) == ".git":
        continue
    previous = baseline / relative
    if not previous.is_file() or previous.read_bytes() != file.read_bytes():
        assert file.suffix not in {".pk8", ".p7b", ".key", ".pem", ".jks", ".keystore", ".p12", ".pfx"}, relative
        changes.append(str(relative))
print(f"Protected runtime files unchanged: {len(paths)}")
print("Changed source files relative to reconstructed 0.2.8:")
print("\n".join(changes))
