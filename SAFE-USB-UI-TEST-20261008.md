# PSA CarPlay — USB 小幅优化 + 1920×720 首页 UI 测试版

> **独立候选版，不覆盖正在使用的实机成功基线。** 目标是只降低“手动开软件/手动点连接”的操作成本，不改已成功的底层 USB 或 LAN 协议。

## 本次变动（安全范围）

- 在现有 `common/src/main/res/xml/usb_device_filter.xml` 保留 CH341 设备的同时，新增本车机实测 Apple iPhone VID/PID：`1452:4776`（`0x05ac:0x12a8`）。
  - 利用已存在的 Android USB_DEVICE_ATTACHED Activity 意图入口；不绕过系统 USB 权限、iPhone 信任与配对。
  - 只匹配该观测型号，不将所有 Apple USB 设备统统匹配，避免过度唤起。
  - 是否自动弹系统“使用此 USB 设备打开应用”提示、是否实际自动进入投屏，仍由车机 ROM 和用户默认应用设置决定，须实机验证。
- 首页取消 `screenHeightDp / 720` 全局叠加缩放，按 dp 正常显示；保留三列方案：连接、连接方式、**真实已配对蓝牙手机列表**。
- 已配对列表展示系统 BluetoothAdapter 已配对设备；点选只保存目标设备，不冒充已连接。无配对显示空状态。
- 将 Wi‑Fi、系统热点与 USB 诊断从首页移入设置；首页更容易操作。
- 1920×720 (160dpi) 首页应完整显示重要操作；更低的实际 dp 可通过已有 ScrollView 滚动，而不是整体缩小文本。

## 严禁触及

USBMUX、Lockdown/iAP2、NCM/VPN、MFi、Bonjour/AirPlay、视频首帧与音频、ManualHotspotManager、ExistingWifiManager 均保持不变；不重新启用 Direct/P2P 或自动 SoftAP。

## 实机测试清单

1. 保存旧版 APK 与 SHA，先不要卸载旧版本。如应用签名不同，应先准备好回退方式。
2. 在未插 USB 的车机上启动：确认首页正常放大，真实手机列表显示，无伪造数据；设置入口能进入。
3. iPhone 已授权时：插线，观察是否由 Android 唤起 PSA；如果需要系统默认应用授权，按实际提示选择。必须保持 USB 一如既往可手动连接成功。
4. 反复执行拔插 USB 5 次、切换 USB 和 LAN 模式：不得抢占重复会话或让车机重启。计时插线到首帧及手动点击到首帧，不能把提示框耗时当成协议耗时。
5. LAN 再次出画面，验证新的 UI 与 USB 过滤器没有造成回归。
6. 车机热点仍处于待验证状态；本次不宣称修复热点 SSID 读取。
7. 若发生权限弹窗频繁、USB 反复唤起、停止后无法回主页或应用崩溃，立即回退到现用成功 APK。

## 构建说明

新分支 CI 在固定 DiPlay v0.2.10 + PSA formal patch **之后**运行 `scripts/apply_safe_usb_ui_tune.py`。预期候选 APK 为：
`PSA-CarPlay-0.2.15-safe-usb-ui-candidate.apk`。

候选 APK 是否构建成功及实机是否改善，必须查看 GitHub Actions 结果与车机实测；代码提交并不等于已经验证成功。
