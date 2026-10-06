# PSA CarPlay 0.2.11-dev（USB / 同一网络 LAN）

独立修复分支，不合并 main、不发布正式 Release。固定上游提交和临时认证资源注入机制不变。

- 移除 Direct/P2P、自动热点、回退和专属设置/服务；仅保留 USB 与 LAN。
- 依据实际接口/地址归并 Network 句柄，真歧义明确暂停；新增已开启系统热点只读接入。
- 优化 JmDNS 初始探测/公告时序，保留真实发布确认和冲突处理。
- 双栈默认保留，新增仅应用于本APP的IPv4实验对照开关。
- 并行释放双栈Bonjour，旧控制器等待门限与实际清理匹配；不允许未退出就开启新实例。
- 保留离线MFi/iAP2/AirPlay/USB/NCM/VPN/TUN和音视频实现；阶段计时及网络元数据诊断加强。

包名com.psa.carplay.dev，minSdk28，versionCode211、versionName0.2.11-dev。开发签名需查看APK-COMPATIBILITY.txt；与旧开发版覆盖兼容不能假定，先备份诊断及设置。测试/构建结果以本提交的Actions为准。

旧Direct/热点模式升级后映射为LAN，首次打开请在主设置保存当前LAN参数，再在系统建立网络。可选择默认双栈或IPv4实验；开关只在会话完全停止后修改。系统热点隐藏信息读取受固件权限影响，不可证明身份时拒绝继续。

详见LAN-ROOT-CAUSE-0.2.11.md及CHANGED-SOURCE-0.2.11.txt。实车性能、WAN因果、iPhone地址重试、厂商热点只读接口及重复连接稳定性仍待验证。
