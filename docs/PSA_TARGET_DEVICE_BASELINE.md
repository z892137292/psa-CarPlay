# PSA 目标车机兼容性基线（测试候选）

代码基线：`cleanup/psa-formal` 6d781cba09ce9a6aca75a9271aba2028bffc0ecb；音频 PR #11：b67e3625c5831351b7faee4a909edc34f7de48c1。本次仅在其后续分支工作，不覆盖 main 或正式候选。

## 已核对的文件与日志事实

- 原始 `carplay-crash.txt` 102149248 字节。10-08 08:18:15.800 / 08:18:36.645 / 08:19:54.700 / 08:23:12.377 / 08:25:00.430 / 08:30:22.624 / 08:31:13.403 均出现 PSA 进程 `com.psa.carplay.dev` 的 `FATAL EXCEPTION: carplay-audio`。
- 首例证据行 32820–32827：`NoSuchMethodError: No virtual method getAudioAttributes()`，`AudioRenderer.createTrack(AndroidMediaSink.kt:958)`；声明来自 `/system/framework/framework.jar`。它证明此 ROM 缺失该方法，不能由 SDK 版本推定存在。
- 10-08 08:25:14.922 起 `wpa_supplicant` 输出 `p2p0: Failed to initialize driver interface`。这证明系统组件报错，不能单独证明是谁请求了 P2P；重建正式源的静态检查禁止应用创建 P2P/SoftAP。没有修改系统服务。
- 10-06 17:35:48.862 / 17:36:04.984：进程 `com.android.systemui`，USB Permission/Confirm Activity 因 CheckBox 空指针失败。不是 PSA 的 Java 崩溃；授权根因仍未确定。
- 已取得原始 Launcher 样本，哈希及 Manifest 见 `PSA_LAUNCHER_COMPATIBILITY.md`。样本是 HOME APK，不是完整 ROM。

## 用户已确认的实机信息（本轮无 adb 独立复核）

| 项目 | 报告信息 | 适配原则 |
|---|---|---|
| 平台 | spm8666p1_64 | 只写诊断，不作为代码分支常量 |
| Android | Android 9 / API 28 | 最低 SDK 28；实机再次读取 SDK_INT、release/build fingerprint |
| 屏幕 | 1920×720 | 多 DPI 页面回归；实机另测字体缩放、系统栏 |
| Root | su 可用 | 正式 LAN/热点复用不要求 root |
| 外接 AP | 无互联网可用，已有 CarPlay 首帧 | 不要求 INTERNET/VALIDATED 或公网 |
| STA / 热点 | wlan0 / ap0 | 按动态 link/address/STA 证据选择，不写死接口名 |
| 曾用地址 | 192.168.2.21 | DHCP 样例，不固定 IP/网关/SSID |

真实车机已显示过视频首帧；本轮不能把视频链路定性为完全失败，也不能把该历史事实写成新候选实测通过。

## 下一轮待实机核实

记录 `getprop ro.build.version.sdk/release`、board/hardware/fingerprint、`wm size/density`、font_scale；检查权限实际授予、WifiInfo 是否脱敏、STA 与热点并存的 LinkProperties。外接无互联网 AP 验证持续视频/声音、10 次连接/断开/重连、首帧前等待、断开回 PSA 首页、无重启及致命崩溃。USB 后续单独验证设备枚举、VID/PID、hasPermission 与授权广播；本次完全保持 USB 源码。
