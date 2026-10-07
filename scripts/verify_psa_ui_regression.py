#!/usr/bin/env python3
"""Guard restored host initialization and the existing 0.2.11 projection UI."""
import pathlib
import sys

HOST = "common/src/main/java/com/shilapi/xcertplay/CarPlayHostActivity.kt"


def section(source, start, end):
    return source[source.index(start):source.index(end, source.index(start))]


def verify(baseline, candidate):
    old = (baseline / HOST).read_text()
    new = (candidate / HOST).read_text()
    for start, end in [
        ("    override fun onCreate(", "    private fun loadPersistedSettings("),
        ("    private fun buildContentView(", "    private fun buildSettingsMenu("),
        ("    private fun updateDebugOverlays(", "    private fun friendlyStage("),
        ("    private fun friendlyStage(", "    private fun initializeSessionLog("),
    ]:
        assert section(old, start, end) == section(new, start, end), start
    # Explicit-connect must use normal initialization, never restart a fresh host.
    launch = (candidate / "common/src/main/java/com/shilapi/xcertplay/DiPlayActivity.kt").read_text()
    assert '"psa_explicit_connect"' not in launch
    print("PASS: host initialization, preparation layout, visibility and stage text match 0.2.11")


if __name__ == "__main__":
    verify(*map(pathlib.Path, sys.argv[1:3]))
