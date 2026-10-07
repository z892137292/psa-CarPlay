#!/usr/bin/env python3
"""Compare reconstructed working PSA baseline with the transport candidate."""
from pathlib import Path
import sys

baseline, candidate = map(Path, sys.argv[1:3])
allowed = {
    "shared/src/main/java/com/shilapi/xcertplay/transport/Iap2WirelessControlClient.kt",
    "shared/src/main/java/com/shilapi/xcertplay/airplay/AirPlaySession.kt",
    "shared/src/main/java/com/shilapi/xcertplay/media/AndroidMediaSink.kt",
}
protected = []
for directory in ("transport", "airplay", "mfi", "media", "iap2"):
    folder = Path("shared/src/main/java/com/shilapi/xcertplay") / directory
    for file in (baseline / folder).rglob("*"):
        if file.is_file() and str(file.relative_to(baseline)) not in allowed:
            other = candidate / file.relative_to(baseline)
            assert other.is_file() and file.read_bytes() == other.read_bytes(), str(file.relative_to(baseline))
            protected.append(str(file.relative_to(baseline)))

sink=Path("shared/src/main/java/com/shilapi/xcertplay/media/AndroidMediaSink.kt")
assert (candidate/sink).read_text().replace('            report("Audio: first PCM received")\n','') == (baseline/sink).read_text(), "Audio changed beyond first-PCM diagnostics"
controller = Path("shared/src/main/java/com/shilapi/xcertplay/orchestration/CarPlayController.kt")
old, new = (root / controller for root in (baseline,candidate))
before, after = old.read_text(), new.read_text()
# The entire wired bring-up implementation remains byte-identical, not just its helper files.
for start, end in (("    private fun startIphone()", "    private fun isBluetoothHandoffCommand"),):
    assert before[before.index(start):before.index(end)] == after[after.index(start):after.index(end)], "USB bring-up changed"
client=(candidate/"shared/src/main/java/com/shilapi/xcertplay/transport/Iap2WirelessControlClient.kt").read_text()
assert client.index("mfi.run(") < client.index("authenticatedEndpoint?.invoke()"), "network precedes MFi"
wireless=after[after.index("    private fun runWireless"):after.index("    private fun startWirelessTunnelControl")]
assert wireless.index("BoundPhoneSession(") < wireless.index("startWirelessHotspot(generation)"), "network precedes phone binding"
assert "WifiP2pGroupManager(" not in after
assert "boundPhone?.airPlayPeerAddress == null" in after
assert "!wirelessTunnelReady.get() || activeSession == null" in after
assert "oldController?.awaitClosed" in (candidate/"common/src/main/java/com/shilapi/xcertplay/CarPlayHostActivity.kt").read_text()
host=(candidate/"common/src/main/java/com/shilapi/xcertplay/CarPlayHostActivity.kt").read_text()
startup=host[host.index("    override fun onCreate("):host.index("    private fun loadPersistedSettings()") ]
required=("DiPlayBootstrap.ensure(this)","initializeSessionLog()","loadPersistedSettings()","setContentView(buildContentView())","applyFullscreenMode()","adoptBackgroundSession()","requestStartupPrerequisites()")
positions=[startup.index(token) for token in required]
assert positions==sorted(positions), "Host startup initialization order changed"
print("PASS: real onCreate retains original UI, settings, diagnostics and permission startup")
print(f"PASS: {len(protected)} protocol/media/USB/MFi files byte-identical; complete wired controller block byte-identical")
print("PASS: MFi -> PHONE_BOUND -> network ordering, ownership and handoff guards, controller exit gate")
print("Actual source changes:")
for file in sorted(candidate.rglob("*")):
    if not file.is_file() or any(part in {".git","build",".gradle"} for part in file.parts): continue
    relative=file.relative_to(candidate)
    if str(relative)==".git": continue
    old=baseline/relative
    if not old.is_file() or old.read_bytes()!=file.read_bytes(): print(relative)
