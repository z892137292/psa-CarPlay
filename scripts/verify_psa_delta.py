#!/usr/bin/env python3
"""Verify the LAN candidate against the complete PSA 0.2.11 development baseline."""
import pathlib
import sys

baseline, candidate = map(pathlib.Path, sys.argv[1:3])
protected_dirs = [
    "shared/src/main/java/com/shilapi/xcertplay/airplay",
    "shared/src/main/java/com/shilapi/xcertplay/mfi",
    "shared/src/main/java/com/shilapi/xcertplay/transport",
    "shared/src/main/java/com/shilapi/xcertplay/media",
]
protected_files = []
paths = set(protected_files)
for directory in protected_dirs:
    for root in (baseline, candidate):
        paths.update(str(p.relative_to(root)) for p in (root / directory).rglob("*") if p.is_file())
authorized_lifecycle = {
    "shared/src/main/java/com/shilapi/xcertplay/transport/Iap2WirelessControlClient.kt",
    "shared/src/main/java/com/shilapi/xcertplay/airplay/AirPlaySession.kt",
}
paths -= authorized_lifecycle
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
print(f"Protected runtime/encoding checks passed: {len(paths)} (byte-identical protocol/media implementation)")
print("Changed source files relative to reconstructed 0.2.11:")
print("\n".join(changes))

print("Deleted source files relative to reconstructed 0.2.11:")
for file in sorted(baseline.rglob("*")):
    if file.is_file() and ".git" not in file.parts and "build" not in file.parts and ".gradle" not in file.parts and not (candidate / file.relative_to(baseline)).exists():
        print(str(file.relative_to(baseline)))
