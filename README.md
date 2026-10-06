# PSA CarPlay

当前修复分支：**0.2.10-dev / Android 9 同局域网连接优化**，基于完整 0.2.9 Direct 生命周期开发状态。

[构建及测试](https://github.com/z892137292/psa-CarPlay/actions) · [发行说明及实车测试要求](RELEASE-NOTES-0.2.10.md) · [根因分析](LAN-ROOT-CAUSE-0.2.10.md)

固定 DiPlay v0.2.10 提交 `3e43e25c55921bdf5149f5f92851acf202ed353a`，单次应用 `patches/psa-main-0.2.10.patch.gz.b64`。不覆盖 0.2.8/0.2.9 补丁、Tag、Release 或 APK。

本分支通过 Actions 测试后生成独立开发 APK artifact，不自动创建 Release。草稿 [PR #3](https://github.com/z892137292/psa-CarPlay/pull/3) 尚未合并到 main。

LAN 模式请在主设置保存路由器 SSID/密码，两台设备连接同一个 Wi-Fi；不要求外网、不创建 Direct。无法验证当前网络身份时暂停连接，不盲用旧 SSID。

原有 Direct A/B/C/D、热点模式仍保留。已报告 PSA 连接 Direct 后整机重启，请勿用本 LAN 修复 APK 继续尝试该触发条件；系统层故障未修复。各硬件用例仍待真实 PSA 车机实测。

运行认证保持现有流程，仅在临时 runner 内准备；签名私钥、密码、MFi 凭据及其他凭证不得提交公开仓库。
