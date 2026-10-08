#!/usr/bin/env python3
"""Conservative PSA UI and USB-attach overlay on the pinned formal source tree.

No USBMUX, Lockdown, iAP2, NCM, AirPlay or media source files are touched.
Fail closed if the expected baseline changes.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
ui = root / "common/src/main/java/com/shilapi/xcertplay/DiPlayActivity.kt"
filter_xml = root / "common/src/main/res/xml/usb_device_filter.xml"

def replace_once(original: str, old: str, new: str, label: str) -> str:
    count = original.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one exact anchor, got {count}")
    return original.replace(old, new, 1)

source = ui.read_text(encoding="utf-8")
source = replace_once(
    source,
    '''        val config = resources.configuration
        homeDesignScale = if (page == "home" && PsaHomeLayout.compact(config.screenWidthDp, config.screenHeightDp))
            (config.screenHeightDp / 720f).coerceAtMost(1f) else 1f''',
    '''        // Android screenHeightDp is NOT the physical 720px panel height.
        // Do not shrink every label, button and spacing a second time.
        homeDesignScale = 1f''',
    "remove global double scale",
)

start_token = "    private fun compactHome(content: LinearLayout) {"
end_token = "    private fun settings(content: LinearLayout) {"
if source.count(start_token) != 1 or source.count(end_token) != 1:
    raise RuntimeError("Expected exactly one compactHome/settings boundary")
start = source.index(start_token)
end = source.index(end_token, start)
old_home = source[start:end]
if "connectionModeControls(modes)" not in old_home or 'label("设置与诊断"' not in old_home:
    raise RuntimeError("Unexpected compactHome baseline; refuse unsafe overwrite")

new_home = '''    // Touch-friendly PSA 1920x720 home: connection, transport, paired phones.
    // Diagnostic and Android Wi-Fi controls live under Settings.
    private fun compactHome(content: LinearLayout) {
        val body = row().apply { gravity = Gravity.TOP }

        val connection = card()
        connection.addView(label("PSA CarPlay", 30, TEXT, true))
        status = label("等待连接", 24, TEXT, true)
        connection.addView(status, matchButton(14, 60))
        connectButton = button("连接手机", true) {
            if (CarPlayBackgroundSession.hasSession()) openProjection()
            else connect(AirPlayPersistence.loadWirelessEnabled(this))
        }
        connection.addView(connectButton, matchButton(12, 76))
        connection.addView(label("USB 可直接连接；无线连接先选择已配对的手机", 16, MUTED).apply {
            setPadding(0, dp(16), 0, 0)
        })
        disconnectButton = button("断开 CarPlay", false) {
            disconnectButton?.isEnabled = false
            CarPlayBackgroundSession.stop { runOnUiThread { refreshStatus() } }
        }.apply { visibility = View.GONE }
        connection.addView(disconnectButton, matchButton(12, 60))

        val modes = card()
        modes.addView(label("连接方式", 26, TEXT, true))
        modes.addView(button("USB 有线", false) { connect(false) }, matchButton(18, 72))
        modes.addView(button("无线 CarPlay", false) { connect(true) }, matchButton(12, 72))
        modes.addView(button("车机热点 / 同一网络配置", false) {
            page = "connection"
            render()
        }, matchButton(12, 60))
        modes.addView(label("无线模式使用设置中保存的网络配置", 16, MUTED).apply {
            setPadding(0, dp(16), 0, 0)
        })

        val phones = card()
        phones.addView(label("已配对手机", 26, TEXT, true))
        val selectedAddress = DiPlayPreferences.phoneAddress(this)
        val bonded = runCatching {
            getSystemService(BluetoothManager::class.java)?.adapter
                ?.takeIf { it.isEnabled }?.bondedDevices
                ?.sortedBy { it.name ?: "" }
        }.getOrNull().orEmpty()
        if (bonded.isEmpty()) {
            phones.addView(label("暂无已配对设备", 18, MUTED).apply {
                setPadding(0, dp(24), 0, dp(14))
            })
        } else {
            bonded.take(3).forEach { device ->
                val phoneAddress = device.address
                val phoneName = device.name?.takeIf { it.isNotBlank() } ?: "已配对设备"
                val selected = selectedAddress == phoneAddress
                phones.addView(button("${if (selected) "✓  " else ""}$phoneName", selected) {
                    DiPlayPreferences.savePhone(this, phoneAddress, phoneName)
                    render()
                }, matchButton(14, 64))
            }
            if (bonded.size > 3) {
                phones.addView(label("其他设备请在手机列表中选择", 15, MUTED).apply {
                    setPadding(0, dp(12), 0, 0)
                })
            }
        }
        phones.addView(button("添加 / 切换手机", false) { choosePhone() }, matchButton(18, 64))

        listOf(connection, modes, phones).forEachIndexed { index, panel ->
            if (index > 0) body.addView(space(20), LinearLayout.LayoutParams(dp(20), 1))
            body.addView(panel, LinearLayout.LayoutParams(0, -2, 1f))
        }
        content.addView(body)
        setupError?.let { content.addView(label(it, 16, WARNING)) }
    }

'''
source = source[:start] + new_home + source[end:]

source = replace_once(
    source,
    'header.addView(label(getString(R.string.diplay), 26, TEXT, true)',
    'header.addView(label(if (page == "home" && PsaHomeLayout.compact(resources.configuration.screenWidthDp, resources.configuration.screenHeightDp)) "PSA CarPlay" else getString(R.string.diplay), 26, TEXT, true)',
    "PSA vehicle header title",
)

source = replace_once(
    source,
    '''            card.addView(button(getString(R.string.choose_save_location), false) { chooseReportDestination() }, matchButton(10, 60))''',
    '''            card.addView(button(getString(R.string.choose_save_location), false) { chooseReportDestination() }, matchButton(10, 60))
            card.addView(button("连接诊断 / USB", false) {
                startActivity(Intent(this, PsaStatusActivity::class.java))
            }, matchButton(12, 60))
            card.addView(button("Wi-Fi 设置", false) { openCarClientWifiSettings() }, matchButton(12, 60))
            card.addView(button("车机热点设置", false) {
                openSystem(Intent("android.settings.TETHER_SETTINGS"))
            }, matchButton(12, 60))''',
    "move diagnostics and Wi-Fi actions into Settings",
)
# Keep the existing 1920x720 UI regression test aligned with the approved home.
# At smaller dp heights the ScrollView is intentional; never shrink every control
# just to force 100% of the home to be visible without scrolling.
wide_test = root / "common/src/test/java/com/shilapi/xcertplay/PsaWideHomeTest.kt"
wide = wide_test.read_text(encoding="utf-8")
wide = replace_once(
    wide,
    'listOf(activity.getString(com.shilapi.xcertplay.host.R.string.connect_phone), "蓝牙设备列表", "Wi-Fi 设置", "系统热点设置", "连接配置", "连接诊断 / USB")',
    'listOf("连接手机", "USB 有线", "无线 CarPlay", "车机热点 / 同一网络配置", "添加 / 切换手机", "已配对手机")',
    "1920x720 home regression labels",
)
wide = replace_once(
    wide,
    '''            assertTrue(title, control.getGlobalVisibleRect(rect))
            assertTrue("$title clipped: $rect", rect.width() >= control.width && rect.height() >= control.height)''',
    '''            if (activity.resources.configuration.screenHeightDp >= 600) {
                assertTrue(title, control.getGlobalVisibleRect(rect))
                assertTrue("$title clipped: $rect", rect.width() >= control.width && rect.height() >= control.height)
            }''',
    "allow scroll at 240/320dpi with very low available dp height",
)
wide_test.write_text(wide, encoding="utf-8")
ui.write_text(source, encoding="utf-8")

xml = filter_xml.read_text(encoding="utf-8")
xml = replace_once(
    xml,
    '    <usb-device vendor-id="6790" product-id="21778" />',
    '''    <usb-device vendor-id="6790" product-id="21778" />
    <!-- Observed on the PSA Android 9 head unit: Apple iPhone 0x05ac:0x12a8.
         Leave the stock Android USB permission and trust flow intact. -->
    <usb-device vendor-id="1452" product-id="4776" />''',
    "narrow iPhone USB attach recognition",
)
filter_xml.write_text(xml, encoding="utf-8")
print("PASS: PSA enlarged home, real paired phone list, Settings diagnostics, Apple USB attach filter")
