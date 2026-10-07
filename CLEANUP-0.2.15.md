# 清理及交付记录 — PSA 0.2.15

## 基线与回滚

- PSA 最新 UI/LAN 修复基线：c638f50a49d3f0386b95726ebcca37fdb1bda20b（0.2.12 分支）。main 仍是 0.2.8，未用旧版替代最新修复。
- 固定源码底座 DiPlay 0.2.10：3e43e25c55921bdf5149f5f92851acf202ed353a。
- 已对照 DiPlay 0.2.13 / 0.2.14：后者增加大量媒体、旋转、BYD 功能，未整体移植；携带 0.2.13 closed-TUN 错误边界修复和四项双 SDK 回归。
- 回滚标签 rollback/psa-before-formal-20261008，由 CI 开始阶段推送；原仓库已本地 git bundle 备份。

## 删除清单

最新 PSA 0.2.12 分支此前已移除主实验网络控制器。本次恢复完整分支，清除剩余 manifest、文案和历史重建入口，最终单份补丁不含下列旧模块。不能将此前已移除文件声称为本次新删除。

从固定底座到最终版的删除文件：

- `common/src/test/java/com/shilapi/xcertplay/LocalOnlyHotspotManagerTest.kt`
- `common/src/test/java/com/shilapi/xcertplay/WifiP2pGroupManagerTest.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/CarHotspotStatus.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/HotspotInterfaceBssid.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/LegacyHotspotRadio.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/LocalOnlyHotspotInterfacePolicy.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/LocalOnlyHotspotManager.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/LocalOnlyHotspotRadioInfo.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/P2pConfigurationMemory.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/P2pOwnership.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/P2pStartupRecovery.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/WifiP2pGroupManager.kt`
- `shared/src/main/java/com/shilapi/xcertplay/network/WirelessHotspotManager.kt`
- `shared/src/test/java/com/shilapi/xcertplay/network/HotspotInterfaceBssidTest.kt`
- `shared/src/test/java/com/shilapi/xcertplay/network/LegacyHotspotRadioTest.kt`
- `shared/src/test/java/com/shilapi/xcertplay/network/LocalOnlyHotspotInterfacePolicyTest.kt`
- `shared/src/test/java/com/shilapi/xcertplay/network/LocalOnlyHotspotRadioInfoTest.kt`
- `shared/src/test/java/com/shilapi/xcertplay/network/P2pOwnershipTest.kt`
- `shared/src/test/java/com/shilapi/xcertplay/network/P2pStartupRecoveryTest.kt`
- `shared/src/test/java/com/shilapi/xcertplay/network/WirelessHotspotManagerTest.kt`
- `shared/src/test/java/com/shilapi/xcertplay/orchestration/ManualHotspotConfigTest.kt`
- `shared/src/test/java/com/shilapi/xcertplay/orchestration/ManualHotspotValidationTest.kt`

本次额外清除：所有旧 psa-main / psa-test 重建补丁（历史保留在 Git）；P2P manifest hardware feature；各语言 wi_fi_p2p_5_ghz 设置资源和兼容性文案中的 P2P/自动热点描述。SystemHotspotManager 及其测试恢复为 ManualHotspotManager，单实现，Controller 直接调用它。RootSoftApBackend / AndroidApiSoftApBackend 在重建基线不存在，已扫描最终源码确认无引用，未伪造删除。

## 保留清单与依赖

| 正式入口 | 依赖与保留行为 |
| --- | --- |
| USB | USBMUX → iAP2 → NCM → VPN / IPv6 bridge → AirPlay；MFi、USB 授权和诊断完整保留 |
| 车机热点 | Bluetooth bootstrap / MFi / PHONE_BOUND → ManualHotspotManager 只读系统现有 AP → Bonjour / AirPlay |
| Existing LAN | 同一蓝牙鉴权 → ExistingWifiManager → 实际 station 接口及 SSID/BSSID 校验 → Bonjour / AirPlay |
| 画面与声音 | type-130、H.264、AAC、触摸及既有编码参数；不修改旋转策略 |
| 生命周期 | 旧 Controller 清理 gate；断线回首页；主视频 FIRST_FRAME 才隐藏准备面板 |
| UI | 1920×720 比例三列首页；真实已配对蓝牙列表；Wi-Fi/热点设置及连接诊断 |

本地 MFi 含 experimental 字样但仍有效，保留全部实现；Android 旧 WifiInfo / WifiConfiguration 兼容读取、type-130 仪表和现有设置同样保留。未依据名称批量删除。

## 验证状态

本地：XML/失效引用/禁止网络创建 API/必需模块检查通过；git diff --check 通过。Gradle 发行包下载被当前环境网络限制，改用 GitHub Actions 执行真实编译及完整单元测试/lint。不能把静态检查替代构建。

Actions 执行 AGENTS.md 要求的 shared/common/home 全量单元测试，mobile/home/maphost lint 与三个 assembleDebug，再生成有运行认证输入的 assembleStandaloneDebug；失败也上传 XML 和 lint 证据。结果以对应 commit 的实际 run 为准，尚未完成时不写“通过”。新增回归：主首帧/仪表帧/旧回调防黑屏、1920×720 操作入口完整可见、USB TUN 提前关闭。保留热点身份、旧控制器 gate、LAN 身份、iAP2/MFi/AirPlay/USB 测试。

## 实机待验证

- PSA 1920×720 屏幕真实布局、字体缩放、触摸；非首页配置长页可滚动。
- 真实已配对设备、蓝牙权限及 PHONE_BOUND；普通热点原成功连接回归。
- PSA ROM 对标准 Wi-Fi / TETHER_SETTINGS 的跳转映射。
- 系统热点字段和接口：可读时实时优先，不可读时明确待确认；SSID 和密码不伪装自动读取。
- Existing LAN 当前 SSID/BSSID / 权限；无互联网的局域网接入。
- USB 数据口、授权、VPN/NCM、实际出画面和声音。
- 首帧之前/失败时保持等待 UI，断线回主页，快速重连不重叠 Controller；日志与真实画面一致。

APK 是正式架构的实机候选包，开发签名；正式签名和硬件验收尚未完成。旧成功普通热点实测不可被本次编译推定为已回归。
