# PSA CarPlay 0.2.15：实际 UI 与首帧显示控制

本次以已恢复真实启动流程的 commit `265775013acbb20c720d280600b466261c81624f`（versionCode 215）为 UI 改造基准，在当前 Bluetooth/SoftAP 开发分支继续修改。完整 Android 源码仍由原有 pinned upstream + full patch 重建，不是 Demo。

## 黑屏原因及修复

上一轮 SoftAP 修改曾误删 Host onCreate 初始化，已在 215 恢复。这次检查到原显示控制仍把 stream active 当作画面就绪；该回调只能证明流建立，不能证明 TextureView 已显示图像。Surface 重建后沿用旧的 ready 状态也可能暴露空白生产者。

主页面先 render，再后台进行实际认证资产准备和自动连接。Host 保留独立 Activity 以复用已有媒体生命周期，但其 onCreate 在权限/网络工作之前安装完整、可操作的同款 UI Shell。真正 TextureView 一直附着在不透明 UI 后面，使 MediaCodec 能正常渲染；不能在首帧之前将生产者设为 INVISIBLE 后又等待其更新，否则形成死锁。

`CarPlayUiState.firstFrameReceived` 需要同时满足当前 generation 的解码器 `Video: first frame rendered` 回调和当前 TextureView 的新更新。`CarPlayHostActivity.createSessionListener().onDebugLog` 记录解码证明，`textureListener.onSurfaceTextureUpdated` 确认当前输出，`updateDebugOverlays` 以 180ms 淡出正常页面。AirPlay active、SETUP、stream active 都不会单独隐藏页面。取消/失败/断线先关闭显示 gate，再异步拆除 controller；旧 controller 未退出时禁止新连接。

AirPlay active 后 20 秒无当前首帧，保留正常页面并显示“未收到 CarPlay 画面，请重新连接”，提供取消、重试和网络设置。返回前台/重新附着 Surface 时保存真实 decoder proof，仍等待新 TextureView 更新，并重新启动超时保护。重复 session-active 回调不清除已显示的真实首帧。

## UI 与真实设备

`CarPlayShell` 使用普通 Android View、系统 sans-serif、深色背景、大圆角卡片、固定五项导航（CarPlay/手机/连接/设置/诊断）、至少 48dp 触控区域。无 Apple 字体或商标资源。设置保留原视频、音频、HUD 等功能；详细选项归入高级。工程状态集中在诊断页面。

`BluetoothPhoneRepository` 读取 Android BluetoothManager.adapter.bondedDevices，Android 12+ 检查 BLUETOOTH_CONNECT；只读实际 isConnected 和保护的 ACL/配对广播刷新。系统不提供连接状态时显示待确认，不伪造已连接。排序为 BoundPhoneSession、当前已连接、已配对 iPhone、其他设备。设备地址只在详情显示。无已配对 iPhone 时提供真实系统蓝牙设置入口。

用户选择写入一次性的 next_phone_address，在下一轮真实 bootstrap 消耗；自动候选顺序仍为已连接、最近实际首帧成功、保存的优先设备。每次真实 CarPlay 连接重新创建 BoundPhoneSession，不永久锁定设备。

## 保留范围

正式连接模式仍是 AUTO、WIRELESS_AP、USB、EXISTING_LAN。默认 AP 使用新增 `ManualHotspotManager` 对原 `SystemHotspotManager` 的委托，保留真实热点识别、人工参数确认和地址检查。原实现未删除、未改写。无可用系统热点时页面显示明确提示；自动创建专用热点作为高级显式选项保留。Wi-Fi Direct 没有正常设置项、AUTO 路由或自动启动。

USB controller 完整 startIphone 代码块与 215 字节一致。全部现有 AirPlay、USBMUX、NCM、iAP2、MFi、视频、音频、触摸协议实现与 215 字节一致；原 Existing LAN、SystemHotspotManager 也未修改。Controller 仅增加 UI 只读快照、一次候选偏好选择、真实首帧后的最近成功记录，以及手动热点委托。

## 文件与差异

本次 UI 源文件：AirPlayPersistence.kt、BluetoothPhoneRepository.kt、CarPlayHostActivity.kt、CarPlayShell.kt、CarPlayUiState.kt、DiPlayActivity.kt、ManualHotspotManager.kt、CarPlayController.kt。mobile/build.gradle.kts 仅更新开发版版本号。新增/更新四组 UI 测试及热点偏好迁移测试。完整文件名在 `PSA-UI-SOURCE-CHECK.txt`；独立 UI 差异为 `patches/psa-0.2.14-ui-fix-to-0.2.15-ui.diff`。旧 215 full patch 仅用于回归比较，当前构建仍使用最新 full patch。

## 验证边界

Actions 执行项目已有协议/连接/USB/媒体测试、UI 状态及真实 Activity 生命周期测试、Debug APK 构建，以及 shared/common/mobile 全量 lint。保留原有 lint 报告并拒绝任何新增 error，不宣称旧项目 lint 零错误。

安装到 Android 9 模拟器后，脚本读取实际 UI hierarchy、截图与 logcat，检查冷启动、无手机、真实空蓝牙列表、点击连接仍有取消按钮、10 次取消/重连、方向变化、前台重入、USB 未插入。它不注入虚假配对、AirPlay 或首帧事件。具体通过结果以构建产物 `emulator-ui/RESULT.json` 为准；未生成该文件则不能宣称安装验证成功。

真实 iPhone 配对/选择、PHONE_BOUND、热点联网、AirPlay 无首帧超时、H264 首帧后切换、视频/音频/触摸、真实断线、USB 成功及拔插、活动 session 横屏重建、Existing LAN 成功，需要车机与 iPhone 实测。模拟器没有这些设备，不能用单元测试冒充完成。
