#!/usr/bin/env python3
"""Prove the USB-only candidate changes exactly one production file."""
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1])
base = "6fb0fa4a09e77a84a437da5159147a6f6141ed61"
production = "shared/src/main/java/com/shilapi/xcertplay/network/Ipv6NcmBridge.kt"
test = "common/src/test/java/com/shilapi/xcertplay/UsbNcmClosedTunTest.kt"

def git(*args):
    return subprocess.check_output(["git", "-C", str(root), *args])

assert git("rev-parse", "HEAD").decode().strip() == base
files = git("ls-tree", "-r", "--name-only", base).decode().splitlines()
changed = []
for path in files:
    candidate = root / path
    if not candidate.is_file() or candidate.read_bytes() != git("show", f"{base}:{path}"):
        changed.append(path)
assert changed == [production], changed
new_files = git("ls-files", "--others", "--exclude-standard").decode().splitlines()
assert new_files == [test], new_files
old = git("show", f"{base}:{production}").decode()
expected = old.replace(
    '        val output = FileOutputStream(tun.fileDescriptor)\n        try {',
    '        try {\n            // USB teardown may close the TUN before this worker begins.\n'
    '            val output = FileOutputStream(tun.fileDescriptor)',
).replace(
    '        val input = FileInputStream(tun.fileDescriptor)\n'
    '        val buffer = ByteArray(TUN_READ_BYTES)\n        try {',
    '        try {\n            // Keep descriptor acquisition inside the existing transport error boundary.\n'
    '            val input = FileInputStream(tun.fileDescriptor)\n'
    '            val buffer = ByteArray(TUN_READ_BYTES)',
)
assert (root / production).read_text() == expected
print(f"PASS: {len(files) - 1} baseline files byte-identical; only USB NCM worker initialization moved into its existing catch boundary")
print("Production: " + production)
print("New test: " + test)
