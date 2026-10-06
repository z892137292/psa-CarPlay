# PSA CarPlay

当前修复分支：**0.2.9-dev / Android 9 Direct 生命周期与安全诊断**。

[构建及测试](https://github.com/z892137292/psa-CarPlay/actions) · [发行说明及实车测试要求](RELEASE-NOTES-0.2.9.md)

固定 DiPlay v0.2.10 提交 `3e43e25c55921bdf5149f5f92851acf202ed353a`，单次应用 `patches/psa-main-0.2.9.patch.gz.b64`。不覆盖 0.2.8 补丁、Tag、Release 或 APK。

本分支通过 Actions 测试后生成独立开发 APK artifact；只有明确手动执行 workflow_dispatch 才创建独立 0.2.9 预发布，禁止覆盖同名资产。

默认 A（仅 Direct 网络），设置中依次选择 B/C/D。Android 9 无法证明进程重启后的系统 Group 应用归属时，拒绝接管或删除。车机稳定性及各硬件用例仍待真实 PSA 车机实测。

运行认证保持现有流程，仅在临时 runner 内准备；签名私钥、密码、MFi 凭据及其他凭证不得提交公开仓库。
