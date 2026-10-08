# PSA CarPlay 车机日志定点修复（2026-10-08）

## 已有实机证据
- 车机于 08:18:15、08:18:36、08:19:54、08:23:12、08:25:00、08:30:22、08:31:13 共七次出现 `FATAL EXCEPTION: carplay-audio`。
- 进程：`com.psa.carplay.dev`；`java.lang.NoSuchMethodError: AudioTrack.getAudioAttributes()`；`AudioRenderer.createTrack(AndroidMediaSink.kt:958)`。
- 因工作线程未捕获 `LinkageError`，应用被系统终止（08:30:22 出现 `appCrashed` 和 `Force finishing activity`）。

## 此分支修复
1. 创建音轨时保存音频路由属性，不再通过 `built.audioAttributes` / `AudioTrack.getAudioAttributes()` 查询 ROM 不提供的方法。
2. 当旧式 streamType 被 ROM 拒绝而回退 usage-based `AudioTrack` 时，同步更新所保存的 AudioAttributes，以保持 AudioFocus 路由一致。
3. 音频 worker 单独处理 `LinkageError`，记录缺失 ROM API 并安全释放资源，避免未捕获错误直接杀死 CarPlay 进程。其他运行时异常仍按原流程处理。
4. CI 在现有 PSA 0.2.15 正式候选单份基线补丁之后应用本定点修复，运行现有完整测试、lint、构建，并检查已移除不兼容 getter。

## 暂未修复/不可冒充 PSA 缺陷
- 大量 `WifiP2pNative / WifiP2pService` 错误来自 Android 系统服务，不可仅凭日志认定 PSA 0.2.15 触发。正式候选已从应用源移除实验 P2P，禁止重新引入它，也不修改系统 Wi-Fi 服务。
- `com.android.systemui` 的 `UsbPermissionActivity/UsbConfirmActivity` 空指针来自车机 ROM，不能将其作为 PSA Java 崩溃直接修改系统组件。
- 本修复**不修改** USB 权限、USBMUX、iAP2、NCM/VPN、Bluetooth、MFi、Existing LAN、ManualHotspotManager、AirPlay 视频协议和首帧 UI。

## 待实际车机验证
- USB 暂时独立排查，以真实 Android `UsbManager.hasPermission()`、PID/VID、权限广播及 USBMUX 数据为准，不依赖外部盒子/第三方实现的推断。
- 在真实车机使用外接无互联网 AP，验证画面出现后持续稳定运行、声音可用、断开返回首页和连续重连。
- 检查日志中无 `NoSuchMethodError: AudioTrack.getAudioAttributes` 和未捕获 `carplay-audio` 致命崩溃；CI 通过不能代替实机确认。
- 实验用 `logcat > file` 属于用户显式录制，长期运行会无限增长；停止采集后单独整理并删除副本，不能凭这一文件推断应用自身在持续落盘。
