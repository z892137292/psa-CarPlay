#!/usr/bin/env python3
"""PSA experimental augmentation applied to the pinned DiPlay 0.2.10 + PSA base.
No device settings are written. If a source anchor changes, fail the CI build.
"""
from pathlib import Path

ROOT = Path("upstream")
def edit(rel, before, after):
    p = ROOT / rel
    s = p.read_text()
    n = s.count(before)
    if n != 1:
        raise RuntimeError(f"{rel}: expected one matching anchor, got {n}: {before[:80]!r}")
    p.write_text(s.replace(before, after))

network = ROOT / "shared/src/main/java/com/shilapi/xcertplay/network/PsaHotspotDiscovery.kt"
network.write_text("""package com.shilapi.xcertplay.network

import android.content.Context
import android.net.wifi.WifiConfiguration
import android.net.wifi.WifiManager

/**
 * Read the car-owned legacy SoftAP configuration on Android 9 if vendor permissions
 * allow. Never change the car hotspot, log credentials, or request root.
 */
object PsaHotspotDiscovery {
    data class Live(val ssid: String, val passphrase: String?)

    @Suppress("DEPRECATION")
    fun read(context: Context): Live? {
        val manager = context.applicationContext.getSystemService(WifiManager::class.java)
            ?: return null
        val config = try {
            WifiManager::class.java.getMethod("getWifiApConfiguration")
                .invoke(manager) as? WifiConfiguration
        } catch (_: Throwable) {
            null // Android hidden-API policy or vendor permission denied.
        } ?: return null
        val ssid = config.SSID?.trim('"')?.takeIf { it.isNotBlank() } ?: return null
        val key = config.preSharedKey?.trim('"')?.takeIf {
            it.length in 8..63 && it != "********" && it != "<unknown ssid>"
        }
        val open = config.allowedKeyManagement?.get(WifiConfiguration.KeyMgmt.NONE) == true
        return Live(ssid, if (open) "" else key)
    }
}
""")

telemetry = ROOT / "shared/src/main/java/com/shilapi/xcertplay/media/PsaVideoTelemetry.kt"
telemetry.write_text("""package com.shilapi.xcertplay.media

import android.os.SystemClock

/** Five-second, non-payload video measurements. Output release != physical display vsync. */
object PsaVideoTelemetry {
    @Volatile private var last: String = "等待视频样本（每5秒更新）"
    @Volatile private var updatedAt: Long = 0L

    fun update(
        incomingFps: Double,
        outputFps: Double,
        gapMs: Long,
        queueMs: Long,
        recoveries: Int,
    ) {
        val verdict = when {
            incomingFps < 6.0 -> "输入帧少：静止界面/网络或手机侧待确认"
            queueMs > 100 || (incomingFps > 15 && outputFps < incomingFps * 0.75) ->
                "解码队列/车机处理可能受限"
            gapMs > 140 && queueMs < 60 ->
                "输入帧到达不均匀：检查无线抖动或手机编码"
            recoveries > 0 -> "视频链路发生恢复；检查详细日志"
            else -> "本时间窗口内未见明显瓶颈"
        }
        last = "输入 %.1f fps / 送屏 %.1f fps\\n最大到帧间隔 %d ms / 最大排队 %d ms\\n恢复 %d 次\\n%s"
            .format(incomingFps, outputFps, gapMs, queueMs, recoveries, verdict)
        updatedAt = SystemClock.elapsedRealtime()
    }

    fun snapshot(): String {
        val age = SystemClock.elapsedRealtime() - updatedAt
        return if (updatedAt == 0L || age > 15000L) "暂无近期视频样本（可能未连接或画面静止）"
        else last + "\\n样本更新于 " + (age / 1000L) + " 秒前"
    }
}
""")

v = "shared/src/main/java/com/shilapi/xcertplay/media/VideoStats.kt"
edit(v,
"""    private var maxArrivalGapNs = 0L
""",
"""    private var maxArrivalGapNs = 0L
    private var maxQueueAgeNs = 0L
""")
edit(v,
"""    @Synchronized fun onRendered() { rendered++ }
""",
"""    @Synchronized fun onRendered() { rendered++ }

    @Synchronized fun onDequeued(ageNs: Long) {
        if (ageNs >= 0L) maxQueueAgeNs = maxOf(maxQueueAgeNs, ageNs)
    }
""")
edit(v,
"""        Log.i(TAG, line)
        windowStartNs = now
""",
"""        Log.i(TAG, line)
        if (label.isEmpty()) {
            PsaVideoTelemetry.update(
                received / seconds, rendered / seconds,
                maxArrivalGapNs / 1_000_000, maxQueueAgeNs / 1_000_000, recoveries,
            )
            Log.i("PSA-VideoPerf", PsaVideoTelemetry.snapshot().replace("\\\\n", " | "))
        }
        windowStartNs = now
""")
edit(v,
"""        received = 0; rendered = 0; recoveries = 0; bytes = 0; maxArrivalGapNs = 0
""",
"""        received = 0; rendered = 0; recoveries = 0; bytes = 0; maxArrivalGapNs = 0; maxQueueAgeNs = 0
""")
decoder = "shared/src/main/java/com/shilapi/xcertplay/media/AndroidMediaSink.kt"
edit(decoder,
"""                        is VideoJob.Frame -> {
                            if (System.nanoTime() - job.receivedNs > MAX_FRAME_AGE_NS) {
""",
"""                        is VideoJob.Frame -> {
                            stats.onDequeued(System.nanoTime() - job.receivedNs)
                            if (System.nanoTime() - job.receivedNs > MAX_FRAME_AGE_NS) {
""")

controller = "shared/src/main/java/com/shilapi/xcertplay/orchestration/CarPlayController.kt"
edit(controller,
"""            WirelessHotspotMode.MANUAL -> ManualHotspotManager(
                context = appContext,
                ssid = config.manualHotspotSsid
                    ?: throw IOException("Manual hotspot SSID is not configured"),
                passphrase = config.manualHotspotPassphrase.orEmpty(),
                band = config.manualHotspotBand,
                channel = config.manualHotspotChannel,
                security = config.manualHotspotSecurity,
                onDiagnostic = ::debugLog,
            )
""",
"""            WirelessHotspotMode.MANUAL -> {
                val live = com.shilapi.xcertplay.network.PsaHotspotDiscovery.read(appContext)
                val configuredSsid = config.manualHotspotSsid
                if (live != null && live.passphrase == null &&
                    live.ssid != configuredSsid) {
                    throw IOException("PSA hotspot name changed, password cannot be read; enter it once")
                }
                val secret = live?.passphrase ?: config.manualHotspotPassphrase.orEmpty()
                val name = live?.ssid ?: configuredSsid
                    ?: throw IOException("PSA hotspot name unavailable; enter it once")
                debugLog(
                    "PSA hotspot auto-detect readable=" + (live != null) +
                        " credentialReadable=" + (live?.passphrase != null) +
                        " (secrets redacted)"
                )
                ManualHotspotManager(
                    context = appContext,
                    ssid = name,
                    passphrase = secret,
                    band = com.shilapi.xcertplay.orchestration.ManualHotspotBand.AUTO,
                    channel = 0,
                    security = com.shilapi.xcertplay.orchestration.ManualHotspotValidation.securityFor(secret),
                    onDiagnostic = ::debugLog,
                )
            }
""")

activity = "common/src/main/java/com/shilapi/xcertplay/DiPlayActivity.kt"
edit(activity,
"""    private fun connect(wireless: Boolean) {
        if (wireless && pendingCarHotspotSetup)""",
"""    private fun connect(wireless: Boolean) {
        if (wireless && AirPlayPersistence.loadWirelessHotspotMode(this) == WirelessHotspotMode.MANUAL) {
            val live = com.shilapi.xcertplay.network.PsaHotspotDiscovery.read(this)
            if (live != null && live.passphrase != null) {
                saveHotspotCredentials(live.ssid, live.passphrase)
                pendingCarHotspotSetup = false
            } else if (live != null && live.ssid != storedSsid()) {
                pendingCarHotspotSetup = true
                toast("已识别车机热点名称，但系统不允许读取密码，请填写一次")
            }
        }
        if (wireless && pendingCarHotspotSetup)""")
edit(activity,
"""            parent.addView(label(if (pendingCarHotspotSetup) getString(R.string.finish_setup_save_your_hotspot_details_to_use_this_mode)""",
"""            parent.addView(button("自动读取当前车机热点", false) {
                val live = com.shilapi.xcertplay.network.PsaHotspotDiscovery.read(this)
                when {
                    live == null -> toast("系统未开放热点配置读取权限，保留手动设置")
                    live.passphrase == null -> toast("识别到 " + live.ssid + "，密码不可读取，需要手动填一次")
                    else -> {
                        saveHotspotCredentials(live.ssid, live.passphrase)
                        pendingCarHotspotSetup = false
                        applyWirelessLink(WirelessHotspotMode.MANUAL)
                    }
                }
            }, matchButton(12, 60))
            parent.addView(label(if (pendingCarHotspotSetup) getString(R.string.finish_setup_save_your_hotspot_details_to_use_this_mode)""")

host = "common/src/main/java/com/shilapi/xcertplay/CarPlayHostActivity.kt"
edit(host,
"""            settingsCategoryHeader(getString(R.string.diagnostics)),
""",
"""            settingsCategoryHeader(getString(R.string.diagnostics)),
""") if False else None

# This is an in-menu, manual refresh (not a high-frequency UI timer).
edit(host,
"""        content.addView(
            buildDebugLogsSection(),
""",
"""        val psaPerfText = menuText(
            com.shilapi.xcertplay.media.PsaVideoTelemetry.snapshot(), 16f, MENU_SECONDARY
        )
        content.addView(psaPerfText)
        content.addView(Button(this).apply {
            text = "刷新视频性能 / 网络与解码诊断"
            isAllCaps = false
            setOnClickListener {
                psaPerfText.text = com.shilapi.xcertplay.media.PsaVideoTelemetry.snapshot()
            }
        })
        content.addView(
            buildDebugLogsSection(),
""")
print("PSA automatic hotspot and video telemetry overlay: applied")
