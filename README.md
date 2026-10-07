# PSA CarPlay

正式连接架构候选版：USB + Bluetooth bootstrap + 车机现有热点 + Existing LAN。
不创建 Wi-Fi Direct/P2P 或 SoftAP。保留本地 MFi、USBMUX/NCM/VPN/iAP2 和 AirPlay 音视频与触摸。

当前清理版本：0.2.15。基线：PSA 0.2.12 UI 修复分支，使用固定 DiPlay v0.2.10 提交加单份完整补丁重建。0.2.13/0.2.14 已作对照，携带 0.2.13 USB closed-TUN 修复，不混入其他旋转/媒体改动。

见 [变更及实机验收](RELEASE-NOTES-0.2.15.md)、[代码差异](FORMAL-0.2.15-SOURCE.diff)。Actions 输出 APK、全量测试和 lint 证据。编译通过不表示实机验证完成。

回滚标签：`rollback/psa-before-formal-20261008`，指向 `c638f50a49d3f0386b95726ebcca37fdb1bda20b`。
源码补丁不含认证资产或签名私钥；运行资产只在构建临时目录准备。
