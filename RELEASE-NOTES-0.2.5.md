# PSA CarPlay 0.2.5

针对 Android 13 手机 Wi-Fi Direct 已连接但未收到 AirPlay 会话的问题，优先选用 P2P 接口实际 IPv4 地址。AirPlay 监听、Bonjour 和 iAP2 共用该地址；不固定 IP，不修改 Wi-Fi 名称。IPv4 尚未就绪时最多等待 2 秒，保留原 IPv6 后备。

新增地址选择测试。此版需实机验证，不能保证仅地址调整即可出画面。Android 9 P2P 仍为实验模式。开发签名可能与上版不一致，覆盖失败时需卸载旧开发版再安装。
