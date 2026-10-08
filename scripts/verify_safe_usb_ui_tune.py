#!/usr/bin/env python3
"""Non-invasive regression assertions for PSA cockpit UI + USB attach."""
from pathlib import Path
from xml.etree import ElementTree as ET
import sys
root=Path(sys.argv[1])
src=(root/"common/src/main/java/com/shilapi/xcertplay/DiPlayActivity.kt").read_text()
host=(root/"common/src/main/java/com/shilapi/xcertplay/CarPlayHostActivity.kt").read_text()
manifest=(root/"common/src/main/AndroidManifest.xml").read_text()
xml=root/"common/src/main/res/xml/usb_device_filter.xml"
devices={(item.attrib.get("vendor-id"),item.attrib.get("product-id")) for item in ET.parse(xml).getroot()}
assert ("6790","21778") in devices, "Existing CH341 USB MFi filter must remain"
assert ("1452","4776") in devices, "Observed Apple iPhone attach filter missing"
assert "android.hardware.usb.action.USB_DEVICE_ATTACHED" in manifest
assert "android.hardware.usb.action.USB_DEVICE_ATTACHED" in host
assert 'homeDesignScale = 1f' in src
assert "(config.screenHeightDp / 720f).coerceAtMost(1f)" not in src
assert 'connectionModeControls(modes)' not in src
for label in ("已配对手机","暂无已配对设备","USB 有线","同一网络 LAN",
              "车机系统热点","添加 / 切换手机","连接诊断 / USB"):
    assert label in src, f"missing new UI action: {label}"
assert 'bondedDevices' in src and 'DiPlayPreferences.savePhone' in src
assert 'CarPlayBackgroundSession.stop' in src and 'connect(false)' in src
print("PASS: existing USB permission path preserved, observed Apple filter added, no double UI scaling, real paired phones")

assert "mainFirstFrameReady && SCREEN_TYPE_MAIN in activeScreenStreamTypes" in host
assert "FIRST_FRAME_WAIT_MILLIS = 90_000L" in host
assert "firstFrameWaitSuspended" in host and "psa_first_frame_timeout" in src
assert "currentSurfaceTexture !== texture" in host
print("PASS: first-frame gate, recoverable deadline and stale Surface protection retained")

import hashlib
preparation = host[host.index("    private fun buildContentView(): View {"):host.index("    private fun buildSettingsMenu(): View {")]
assert hashlib.sha256(preparation.encode()).hexdigest() == "6a2eaf8257e165f5c3fbd56374ba893b4db1871b60ffa5b136f66f12d8cc06f0", "Original preparation UI must remain intact"
