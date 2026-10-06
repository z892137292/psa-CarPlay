# PSA CarPlay 0.2.10-dev：独立 LAN 连接和分阶段诊断

从完整 PSA 0.2.9 开发源码最小增量修改。固定上游提交不变，新完整补丁 psa-main-0.2.10.patch.gz.b64，旧补丁/Tag/Release 不修改。不创建正式 Release。

- 新增同一 Wi-Fi / LAN 入口与独立路由器参数；不会创建 P2P/热点、加入 Wi-Fi、改默认路由或关闭移动数据。
- 消除 JmDNS 创建中的非必要反向 DNS 依赖，记录 create/register/announce 耗时；LAN 等待本地发布确认后才交接。
- 当前 SSID 优先核验，未知身份只有曾经核验且当前 BSSID 一致才可回退，否则明确失败。Android 13 LAN 请求精确位置；Android 9路径保留。
- IPv4 + scoped link-local IPv6 mDNS/TCP 同地址同端口，监听地址不一致时禁止发送配置；地址变化停止本轮。
- StartSession 2.5秒早期诊断，保留30秒期限；观察到本地注册无效才最多重注册一次；继承旧控制器完全关闭门禁与3次有间隔重试。
- LAN_TIMING 记录 Wi-Fi、Bonjour、RFCOMM、MFi、配置交接、StartSession、TCP、SETUP、首帧/总耗时。
- 不改变现有视频/音频/旋转/MFi认证实现和协议编码；保留 Direct、普通热点、USB、报告保存机制。

详见 LAN-ROOT-CAUSE-0.2.10.md，含证据、未证实假设、源码地图及实机验收步骤。

## 安装与安全边界

包名 com.psa.carplay.dev；versionCode 210，版本0.2.10-dev，minSdk28。GitHub runner开发签名可能与已安装0.2.8/0.2.9不同，必须查看产物 APK-COMPATIBILITY.txt；不能承诺覆盖安装。不要公开上传密码或认证材料。

在主设置选择“同一 Wi-Fi / LAN”，保存当前路由器SSID/密码（开放网络留空），在系统Wi-Fi中手动连接，两端同网络，允许精确位置并开启定位。名称仍不可验证时会停止，不盲用旧参数。

当前固件 Direct iPhone接入重启属于另行系统排查，本次不能解决；不要自动接入 Direct。性能目标和WAN因果尚需实测。自动化与编译结果以同提交Actions附件为准。
