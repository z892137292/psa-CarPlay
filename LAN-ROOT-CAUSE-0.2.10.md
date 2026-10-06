# PSA LAN 快速连接：根因报告与验证边界

## 基线和证据

PSA 基线是开发分支 fix/psa-0.2.9-direct-lifecycle 的 4e8cf8ee145ae914fe50203c62d8fe7ab2230e22，仍从固定 DiPlay v0.2.10 / 3e43e25c55921bdf5149f5f92851acf202ed353a 和完整 PSA 补丁还原。当前 main 尚为 0.2.8；PSA 0.2.9 尚无 Same LAN 模式。本次不整体升级上游；选择性参考 DiPlay v0.2.13 的 ExistingWifiManager、双地址监听、接口绑定 Bonjour。保留 GPL/AGPL 通知与原有认证资源临时注入方式。

用户两份 TXT 的头部明确为原版 DiPlay 0.2.13，Xiaomi Mi 10 Pro / Android 13，不能当成 PSA 实车证据。两份报告包含重复历史片段，不能把它们当独立重复测试样本。日志隐去了地址和 SSID，不能据此核对具体路由器身份或地址一致性。

## 12 秒等待：可证明的调用风险与尚待证实的运行原因

211614 报告中，21:08:00.011 TCP listener 就绪，21:08:12.088 Bonjour started；21:08:39.780→21:08:51.820，21:10:40.741→21:10:52.785 同样约 12 秒。21:16:06.496→21:16:06.533 则仅 37ms。

调用链：CarPlayController.runWireless → CarPlayBonjour.start → JmDNS.create → JmDNSImpl 构造 → HostInfo.newHostInfo。两条地址按 IPv4、IPv6 逐一创建；该路径不走 Android NSD 注册回调。

固定依赖 org.jmdns:jmdns:3.6.3 / 源码 v3.6.3 (93b326381940f3fcd250d770a14a36de4c2dfcda) 的 HostInfo.newHostInfo 即使已有显式 jmdnsName，在判断主机名时仍调用 addr.getHostName()。未命名的 InetAddress 因而可能同步执行反向 DNS；网络 DNS 行为变化可延迟初始化。registerService 的实现提交 Prober，不包含固定 12 秒 sleep。

修复：用 InetAddress.getByAddress(name, bytes) / Inet6Address.getByAddress(name, bytes, scope) 保持字节及 IPv6 scope，显式缓存本地主机名，消除该反向 DNS 查询。逐个记录 create、register、announce 的单调时钟耗时。LAN 等待所有选定地址上的服务状态 isAnnounced 后才进入 RFCOMM/配置交接。注册就绪仅证明本地宣布成功，不声称 iPhone 收到了多播。

**仍待验证：** 两份旧日志没有 JmDNS 内部子调用耗时/线程栈，无法证明当时那 12 秒全部来自反向 DNS，也不能认定 WAN 是唯一原因。新日志可定位剩余等待。

## 30 秒无 TCP：事实，不是已确定的 WAN 根因

212813 报告 21:24:05 启动至 21:24:36.837 超时，后一次 21:24:40→21:25:11.781 也超时；21:25:15.849 同类信道 11 启动却在 21:25:18.574 首帧。MFi 成功、0x5703 和 0x4301 已发送，但无外部 TCP。不能解释成认证失败或用缩短 timeout 解决。

上游 ExistingWifiManager 在 SSID 不可读时仍返回保存的 SSID，未验证当前网络身份。本次改为实时 SSID 匹配，或此前实时验证的 SSID + 当前有效 BSSID 完全匹配；仅保存名字、占位 BSSID、未知 AP 一律 NETWORK_IDENTITY_UNVERIFIED。不验证密码正确性（系统一般不公开当前密码），用户仍须填写路由器真实参数。

identitySource=saved 指的是接收器 AirPlay device identity（未用路由器 BSSID冒充接收器），不是 SSID 验证结果。bonjourAdded/Resolved/connectProbes 是发现 iPhone 的 _carplay-ctrl._tcp 服务及发出 connect probe 的计数，不是本机 _airplay._tcp 发布成功计数。零计数在成功出画面记录也出现，不能单独视为发现失败。

新增 2.5 秒早期检查真实网络/本地发布状态；只在本地注册实际失效时最多重注册一次。30 秒仍无外部 TCP 分类 FIRST_TCP_TIMEOUT，不推断 AP 隔离、DNS或互联网必然是原因。监听地址与公布地址不一致才分类 AIRPLAY_ADDRESS_MISMATCH；真实接口/地址变化才分类 INTERFACE_CHANGED。本地宣布超时才 BONJOUR_TIMEOUT。

## 源码地图

| 阶段 | 代码 |
|---|---|
| LAN 选择/独立参数 | DiPlayActivity.wirelessLinkControls；psa_lan 私有设置 |
| Wi-Fi station 和双栈地址 | ExistingWifiManager.start/validateReady；LanPolicy.kt |
| Bonjour | CarPlayBonjour.start/waitForPublication/refreshInvalidPublication/close |
| TCP 挂接 | CarPlayVpnService.attachWireless/startAirPlayServer/acceptLoop；AirPlayPortSelector.bindAll |
| 蓝牙 RFCOMM | CarPlayController.runWireless/connectBluetoothSocket |
| iAP2、MFi、Wi-Fi配置、StartSession | Iap2WirelessControlClient.run；Iap2MfiAuthenticationClient（认证实现不变） |
| 早期检查、30s期限 | LanStartupEvidence；CarPlayController LAN monitor |
| 代次关闭与有间隔有限重试 | CarPlayController.closeWirelessStack；CarPlayHostActivity.reconnectAfterLoss/restartCarPlay |
| 阶段耗时 | LanAttemptDiagnostics，LAN_TIMING 日志 |

0x5703/0x4301 原始编码逻辑和协议字节保持不变；新增发送前 LAN 有效性检查。0x4301 使用真实监听端口和与 mDNS 同接口的地址列表。MFi、iAP2必需握手没有跳过。Wi-Fi INTERNET/VALIDATED 不作为准入条件；移动数据和系统默认路由不修改。

## 实机验收（未执行）

停车测试。WAN 开/关两组分别至少 10 次；相同路由器、SSID/AP、5GHz固定36或44、40MHz、位置、APP、iOS配置，只切换 WAN。记录首次启动与重连、是否成功、LAN_TIMING first_frame totalMs、bonjour_ready elapsedMs、first_tcp elapsedMs、失败分类；统计成功率/P50/P95，失败不混入成功首帧分布，保留失败数。清除路由器 AP/客户端隔离，记录而非擅自关闭移动数据。

PSA Android 9：授予精确位置并开启定位；先 USB、普通热点回归，再测 LAN 的无外网、有外网、移动数据共存、Wi-Fi断开/换网/重新连接、退出重进、5次重连、音视频触摸和诊断报告。原车 Direct 接入已由用户报告会整机重启，本次不执行 iPhone Direct 接入；Direct 代码保留，不声称固件缺陷已修复。

3–5 秒首帧只是目标，不是实测结果。无法远程控制车机/手机/路由器，所有硬件项目待用户实测。
