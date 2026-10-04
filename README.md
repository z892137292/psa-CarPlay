# PSA CarPlay

当前分支：PSA CarPlay 0.2.1 有线基础开发版，基于 DiPlay v0.2.10。

下载APK：[GitHub Releases](https://github.com/z892137292/psa-CarPlay/releases)
编译状态：[GitHub Actions](https://github.com/z892137292/psa-CarPlay/actions)

源码由固定上游提交与单份分支差异组成。Actions只对原始v0.2.10应用`patches/psa-main-0.2.1.patch.gz.b64`，不应用以前的测试补丁。
完整分支源码可按工作流的materialize步骤重建；上游来源、许可证随源码保留。

运行认证仅沿用此前成功构建流程，从上游发布APK提取到临时runner，不在本仓库存储。
签名密钥、PRIVATE_SIGNING及密码不得提交此公开仓库。
当前构建开发测试APK，包名com.psa.carplay.dev。正式包com.psa.carplay需要私密签名配置。

功能及限制见[版本说明](RELEASE-NOTES-0.2.1.md)。
