# PSA 0.2.11-dev：USB / LAN 精简及无线等待调查

基线是 PSA 0.2.10-dev e2ae72ddce4c3d49a7a4a4fe089d42156b385012；固定上游仍为 DiPlay v0.2.10 / 3e43e25c55921bdf5149f5f92851acf202ed353a。新完整补丁单独保存，不覆盖旧补丁、main、Tag 或 Release。

## 新日志确认的事实

两份报告为 PSA 0.2.10-dev，Xiaomi Mi 10 Pro / Android 13，不能代表 PSA Android 9 实测。223738 报告中多个 Bonjour create 仅 1–17ms、register 0ms，announce 却 5035/5036ms；22:32 首帧 7372ms，22:33 首帧 7800ms，使用 IPv6 的 first_tcp 分别仅 207/297ms；较早连接有约 27 秒 TCP 等待，不能仅凭 IPv6 推定根因。

22:33:46.027 开始退出，22:33:50.039 的 awaitClosed 在 4013ms 返回 false；Bonjour 在 22:33:50.059 完成（4018ms），完整关闭在 22:33:50.082 完成（4055ms）。这次证据支持关闭门限与正常资源退出耗时竞争，不证明控制器永久泄漏。

224752 中旧错误只记录 Network 对象数量，没有对应接口、地址及句柄，不能确认当时是真多 STA 还是重复/残留对象。2/4/8 秒重试不会解决恒定的歧义判断。

## 5 秒的具体代码原因及优化

CarPlayBonjour.start -> JmDNS 3.6.3 Prober.start：新主机尚未 announced 时，三个 probe 使用 1000ms 初始延迟/间隔；随后 Announcer.start 两次公告仍使用 1000ms 延迟/间隔。PSA 0.2.10 等待 isAnnounced，因而观察到约 3+2 秒。不是 Android NSD 回调，也不是固定 sleep(5000)。此前约 12 秒仍有反向 DNS 风险；0.2.10 已给 InetAddress 显式主机名，新日志 create 快，不能把本次 5 秒再归因于 DNS/WAN。

新增仅应用于 psa-lan- 实例的 JmDNS 调度适配：初始探测随机等待 0–250ms，三次探测间隔250ms；保留第三次后的250ms冲突检测窗口，再发送两次相隔1000ms的公告。首次主机/服务两项探测使用快速计划；后续冲突、恢复使用原 Prober 调度，保留原命名冲突、重试、续租、取消逻辑。继续等待真实 isAnnounced，不手动伪造 READY，不跳过发布。

依据为 JmDNS 3.6.3 固定源码和 RFC6762 §8.1/§8.3（https://www.rfc-editor.org/rfc/rfc6762.html）。这依赖 JmDNS 内部扩展接口，升级该依赖必须重新验证。广播接收、慢设备冲突及路由器兼容性仍待实测。

## Network 选择与地址路径

ExistingWifiManager -> LanNetworkSelection：排除 VPN、缺少 LinkProperties/有效接口/地址的历史句柄，以接口+选定地址集合归并；同链路多个句柄选当前 Wi-Fi 默认句柄或等价别名。不同接口/地址仅在有具体默认 Wi-Fi 证据时选择它，否则 NETWORK_AMBIGUOUS，暂停自动重试。蜂窝/VPN默认网络不被当成目标 Wi-Fi；不修改默认路由。

onLost 可只换到相同接口、相同地址的另一存活句柄；真正地址/接口变化结束本轮。仍核验实时 SSID，不可读时必须匹配此前已验证的当前 BSSID。新增候选/链路数、接口、IPv4/IPv6及scope元数据；严格格式的 LAN_ADDRESS 保留真实地址，不输出密码或认证数据。

默认双栈不变；“IPv4 优先实验”仅让本 APP 发布、监听和0x4301地址列表使用实际IPv4，不关闭系统IPv6。两种路径仍沿用相同0x5703/MFi/iAP2编码。27秒为何发生、iPhone是否重试或回退仍未知，必须用同条件对照和包时间线验证。

LAN 可使用已有 Wi-Fi station 或系统设置已开启的热点。后者只读 AP 状态/名称和实际无线接口；不调用启停、配置热点/P2P方法。Android9厂商限制读取真实热点身份时明确失败，不猜测旧身份。外部AP最适合首轮对照。

## 生命周期及架构

最终入口只有 USB 与 LAN。删除 Direct/P2P、自动热点构造器、回退、Direct服务、诊断阶段、热点创建设置和helper模块。旧模式迁移为 LAN，但不把旧 SSID/密码自动冒充当前 LAN。USB、NCM、VPN/TUN、RFCOMM、iAP2、离线 MFi、AirPlay编码和音视频实现保留。

两个 JmDNS 关闭并行发送 goodbye/等待取消，仍等全部完成；失败不会冒充干净退出。控制器门限由4秒改为12秒以容纳依赖自身的有界取消等待，awaitClosed=false时仍禁止创建新实例。一次迟到的成功退出只解除门禁并提示人工重连，不自动启动。真正歧义或身份失败不做2/4/8秒完整重连。

MFi计时改为 identification accepted 后到 authentication accepted，包含整个MFi运行而非仅challenge签名。其余 wifi_ready、bonjour_ready、rfcomm_ready、start_session、first_tcp、first_frame 继续按单调时钟/连接代次记录。

## 上传旧 APK 对照边界

DiPlay-0.2.13.apk SHA256 aed9eac786e7c0e80a2929dc2f0c2e1d0df318ca8fd83ae7c2988a98bb4cd7e6。APK构建元数据指向公开提交6fb0fa4a09e77a84a437da5159147a6f6141ed61，DEX包含ExistingWifiManager、CarPlayBonjour和旧多Wi-Fi错误文本。按该公开提交比较，不将后来tag/main当成二进制的确切实现；未进行完整DEX反编译，不能证明编译/混淆后的所有运行细节一致。旧成功IPv4和新成功IPv6均有日志基础，但WAN、地址优先级的因果未知。

公开提交的实际差异：0.2.13 的 ExistingWifiManager 按 Wi-Fi Network 句柄数量直接拒绝多个对象；地址列表本来就含 IPv4 和有 scope 的链路本地 IPv6，并非纯 IPv4实现。其 CarPlayBonjour.start 在 registerService 后直接进入下一阶段，没有等待真实公告完成。因此旧版较短 Bonjour 返回时间不能等同于服务已可被 iPhone 使用；本次保留就绪屏障，优化内部探测调度，而不照搬旧版过早返回。旧版 dns.close 亦顺序执行并忽略异常，本次等待并行关闭且将异常保留为不干净退出。

## 实测矩阵（未执行）

停车、同一APP/iOS/路由器/SSID/BSSID/位置、5GHz信道44、40MHz。双栈WAN开/关、IPv4实验WAN开/关各10次；记录成功数、bonjour_ready、start_session到first_tcp、first_frame总时长及P50/P95，失败单独计数。不要把重复历史报告算新样本。

Android9回归：USB首次及授权已授予场景、USB/LAN切换5次、LAN网络断开/恢复、退出重进5次、连续连接5次、后台会话唯一性、音视频触摸、诊断保存、系统已启用热点只读接入。检查无P2P/热点创建日志及系统网络切换。

若设备已有tcpdump且获授权，可仅记录包时间/源目的地址/标志（不导出认证或音视频载荷）：`adb shell tcpdump -i wlan0 -n -tttt 'udp port 5353 or tcp portrange 7000-7010'`。对照mDNS公告、SYN/SYN-ACK、IPv4/IPv6重试和实际接口；没有抓包不声称已证明iPhone回退。

3–5秒是目标，不是车机已实现指标；所有PSA、iPhone、路由器硬件验收待实测。
