# 媒体控制恢复时机修复报告

日期：2026-10-14。状态：已构建并通过静态、签名及主机模拟检查；未安装到车机，未做实车验证。

## 基准与保护

基准为上次交付 AndroidPlay-1.2.0-media-ipv4-fix-test.apk，SHA-256 `968c4c2bf8aa9187ae4cd619cb59c4eaf1e4792f0ba002d773cebdf38ca2c311`。实际取回文件、重新计算哈希并创建只读备份；原文件及之前交付均保留。未使用初始母包替代，未触碰已验证 APK。

新包：AndroidPlay-1.2.0-media-timing-fix-test.apk，SHA-256 `f41594931d2a83a2c8b657466923b7b496918d9b5afb1fb0f938c177b236fbc1`。
包名 com.androidplay.app，版本 1.2.0 / 45，minSDK 28、targetSDK 35 均未改变。

## 定位与两处修改

现有前台通知经 CarPlayHostActivity / CarPlayBackgroundSession 转到 AndroidPlayMediaSession.psaSetForeground，再调用 PsaMediaControl.setForeground → 原 Handler → foregroundChanged → restoreOnce → AudioManager.requestAudioFocus → refreshActive → MediaSession.setActive。

旧版 restoreOnce 额外要求 eligible（有歌曲标题或正在播放）。返回前台但手机还没有推送这些信息时，该条件会延迟焦点申请；refreshActive 同样受这个条件限制。这是代码中确认存在的等待点，尚无车机日志证明它是该设备延迟的唯一原因。

只修改 classes3.dex 的 com/shilapi/xcertplay/PsaMediaControl：

1. restoreOnce()V：移除 eligible 等待条件。仍须未关闭、有本次前台切换待处理、正在前台、尚未持有请求；每次明确前台切换最多尝试一次。
2. refreshActive()V：激活条件由 eligible 改为 foreground || eligible；仍须焦点已获准、未暂停、未关闭。

不触发自动播放；焦点拒绝后不循环申请。失焦、后台行为、临时失焦等待系统恢复、按键映射及去重代码保持原样。恢复发生在现有 Handler 处理前台事件并获准焦点时，不承诺固定毫秒时延。

## 检查结果

- ZIP：122 个条目，只有 classes3.dex 内容变化，其余 121 个逐字节一致，无新增或删除条目。
- classes3：比较 228 类、1474 个方法；仅上面两个方法变化，其余 1472 个方法及类字段、注解一致。最终 APK 内 DEX 与完成方法差异检查的 DEX 完全相同。
- 11 个 DEX：头部、文件长度、SHA-1、Adler32、表边界检查通过，修改后 DEX 反汇编通过。
- Manifest、资源、原生库、认证资产内容完全一致；认证材料不单独提取或公开。
- apksigner 验证通过，包括显式 API 28 检查；zipalign 16KB 页对齐检查通过。
- 18 个主机模拟场景、90 项断言通过：连续切换10次、不重复抢占、拒绝焦点、临时失焦、按键映射/去重、后台持有、关闭后回调、无元数据返回立即激活且不自动播放。
- 主机测试运行可读 Java 逻辑；没有 Android ART 执行、真实设备安装或实车测试。标准 MediaSession 的通过不证明 PSA 厂商通道已接收所有方向盘事件。

## 实车待验与风险

明确进入 CarPlay 前台现在会比旧版更早尝试获得媒体焦点，即使手机尚无歌曲信息。这正是本次行为变化；是否会在特定车机的前台生命周期误报时提前中断原车音乐，需要现场确认。没有增加周期抢占、重试、自动播放或厂商按键通道。

待验：首次连接按键、转原车音乐后按键、返回 CarPlay 后首个上一曲/下一曲/播放暂停、10次往返、Siri/导航/通话后恢复、IPv4无线重连及音视频不退化。建议记录进入前台到首个有效按键的时间，以及 PSA-MEDIA 的 foreground / restore result / focus / dispatch 日志；本报告不虚构时间测量或实车结果。

签名和回退见 rollback-media-timing.md；冻结逐项证据见 freeze-diff-report.md。
