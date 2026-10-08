# PSA ROM 专项回归与交付记录

版本状态：0.2.15-ROM 测试候选。基于正式候选 + PR #11，未覆盖 main；最终实机验收尚未执行。

## 最小代码变更

- 保留 PR #11：AudioAttributes 来自构造时的本地变量；fallback 保存其实际 usage 属性；禁止 AudioTrack getter。
- 解码器创建后只有 configure/start 完成才发布；失败释放半初始化资源并交给 worker 明确报告。无效 min buffer / uninitialized track 不再报告 ready。
- Legacy 构造或初始化遇到 ROM LinkageError 可走 usage fallback；worker 原有 Exception/LinkageError 防护保留。释放 audio focus/codec/track 分别保护，某一步失败仍释放后续资源。没有永久关闭音频。
- Existing LAN 用运行时 WifiInfo IPv4 地址筛选 STA，防止热点成为默认网络时误选；地址不可读或 IPv6-only 保留原来的动态选择及歧义检查。无固定设备、接口、SSID、IP、网关；不依赖公网。
- 日志原有 512KiB 轮转与 64 条队列已存在，不是无限文件录制。改为写入前限制大小，按路径共享锁、UI 日志异步写；修正首页 disconnect.log 路径使其纳入导出。disconnect 使用独立轮转文件，避免覆盖音视频证据；成功的周期性详细媒体计数要求诊断模式，故障/首帧/断开/teardown 保留。
- Wi-Fi 设置删除旧 BYD Settings 专属的 HOME 跳转，直接进入系统 Wi-Fi 页面，避免 Launcher 插入任务栈。
- 诊断导出入口已有“软件设置 → 保存诊断报告”，导出 PSA 元数据和脱敏日志；不自动抓取无限 logcat。不声称可读整个系统 Logcat，SystemUI/supplicant 原始错误作为本报告证据单列。

## PR #11 审核与 API 28

去除危险 getter 的修复正确；原始 fallback 属性保留。此前 PR #11 CI run 37712256685 未通过：common 的 3 个 PsaWideHomeTest 在测量子 content 而未布局 decor 窗口时 getGlobalVisibleRect=false。本次修正为测量完整 decor，保留可见区域断言。
AudioTrack.Builder/API23、bufferSizeInFrames/API23、routedDevice/API23、underrunCount/API24，AudioFocusRequest/requestAudioFocus/abandonAudioFocusRequest/API26，MediaCodec configure/start/API16、name/API18 均在 min28 范围；较新 API 必须由 lint 和已有 SDK 条件确认。SDK 存在不证明厂商实现完整，缺失方法用故障注入模拟。

## 测试层级（不能相互替代）

| 要求 | 自动化覆盖 |
|---|---|
| ROM 缺失方法、音频线程 | API28 PsaRomAudioWorkerTest 通过 Shadow 故意抛 NoSuchMethodError，执行真实 AudioRenderer.run，验证报告且不逃逸 |
| AudioTrack/fallback | LegacyAudioFallbackTest + PsaRomAudioGuardTest：构造失败/未初始化/释放缺失方法/fallback；静态属性来源守卫 |
| 解码器失败 | 实际 worker AAC 创建失败模拟；generic initialization 部分 configure 失败释放回归 |
| H.264 Surface/首帧 | CarPlayHostPreparationTest 在 API28/29：PsaSurfaceLifecycleTest 的真实 Android Surface 创建/替换/销毁（无硬件 H.264 解码执行），当前/旧 Texture 更新、销毁、无首帧等待、ALT/stale generation、快速断开重入；未验证硬件解码器 |
| 1920×720 | PsaWideHomeTest：mdpi/240dpi/320dpi，必需按钮全部可见；实机字体缩放/触控仍待验证 |
| Activity 返回/恢复 | PsaLauncherReturnTest 确认 terminal loss 明确回 PSA home、Wi-Fi 不插入 HOME；既有 CarPlayHostDisplaySizeTest 覆盖保留控制器重复进入；真实 Launcher 暂停恢复待实机 |
| 快速断开/资源互斥 | 快速 stream 反复激活/终止；既有 ControllerCloseGateTest、LanBonjourLifecycleTest 检查异步 close 与单控制器 |
| 无互联网 LAN | 既有 API28 LanNetworkManagerTest 切换 INTERNET/VALIDATED 不影响可用性、不改路由 |
| wlan0/ap0 并存 | PsaStationLinkTest：动态地址证据、改名接口、重复 handles、IPv4 不可用；不把接口名写入正式逻辑 |
| Bluetooth handoff | 既有 WirelessHandoffTest、WirelessConnectionProofTest：handoff 后 bootstrap 正常关闭不判会话断开 |
| 禁止实验回归 | verify_formal_tree.py 扫描主源码/Manifest；verify_psa_rom.py 禁止 getter、验证属性/fallback与保留协议源码 SHA256 |
| USB/MFi/协议 | 本次关键源文件逐字节哈希检查，完整既有测试；USB 实机授权与会话另轮验证 |

## 构建记录

本地 Gradle 未执行到编译：下载 Gradle 9.5 时 Network is unreachable。不能算测试通过。GitHub Actions 执行完整 shared/common/home 单测、mobile/home/maphost lint、debug 与 standalone APK；XML 结果、lint、签名、package/minSDK、SHA256 和最终源码差异随 Artifact 保存。首轮专项 CI 37717610995 执行 shared 384 测试，1 个测试因 Kotlin 泛型推导为 Unit 导致断言失败，已显式指定测试资源类型 String；真实 worker 的两项故障注入通过。该轮未执行完全部检查，不交付 APK。最终通过/失败/未执行结果以该候选 commit 对应 Actions 与交付报告为准，尚未完成的检查不写通过。

## 实机待验证清单

API28/build fingerprint、真实 Launcher 冷热启动与返回、DPI/font_scale、H.264 连续播放、音频输出/导航混音、10次连接断开重连、无黑屏/重启/致命崩溃、外接无互联网 AP、STA+系统热点同时存在、Bluetooth交接。USB不修改，下一轮单独抓 VID/PID/重枚举/hasPermission/权限回调/SystemUI错误。
