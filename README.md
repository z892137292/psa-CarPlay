# PSA CarPlay 与热点助手

当前：PSA CarPlay 0.2.2 开发版 + 独立 PSA 热点助手 0.1，Android 9 / API28起。

[APK下载](https://github.com/z892137292/psa-CarPlay/releases/tag/v0.2.2-hotspot-dev)
[编译状态](https://github.com/z892137292/psa-CarPlay/actions)
[使用及限制](RELEASE-NOTES-0.2.2.md)

Actions从固定DiPlay v0.2.10原始提交应用一份分支差异`patches/psa-main-0.2.2.patch.gz.b64`，不叠加旧测试补丁。
热点助手源码在重建源码的hotspothelper模块；它只打开系统设置，不使用ADB/root，不静默开关热点。
签名私钥与密码不得提交本公开仓库。运行认证沿用原流程，只在临时runner中准备。
