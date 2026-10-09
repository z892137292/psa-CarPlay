# AndroidPlay PSA 认证资源核查（2026-10-09）

本地 ANDROIDPLAY_AUTH_ASSETS_DIR 未配置，项目默认 runtime-assets 目录不存在，identity.pk8 与 certificate.p7b 未找到；四项原 release 签名环境变量均未配置。因为没有实际资源，未执行真实文件解析、私钥/证书匹配或 LocalMfiAuthenticationClient.load 验证，不能声称认证资源失效或不存在于其他环境。

DiPlay v0.2.6 的 [README](https://github.com/shihabal3amri/DiPlay/blob/v0.2.6/README.md)、[构建说明](https://github.com/shihabal3amri/DiPlay/blob/v0.2.6/docs/BUILD.md) 与 [第三方声明](https://github.com/shihabal3amri/DiPlay/blob/v0.2.6/docs/THIRD_PARTY_NOTICES.md) 已核对。源码采用开源许可，但作者说明实验认证数据源于 Carlinkit 固件，不作为项目源码重新授权，通用分发的适用性尚未确定。未发现本次使用/再分发授权证明。公开 APK 可下载与历史 MFi 认证成功均不能替代授权记录。

本次不提取第三方私钥、不重打包认证身份，也不修改认证模块。原 AndroidPlayBootstrap 与 LocalMfiAuthenticationClient 保持原状。SDK28/ap0 IPv4 修复保留；之前262项单元测试、Lint和无认证源码包构建已通过。

测试分支的构建入口已补充：

- 成对配置认证Secrets，并记录 ANDROIDPLAY_AUTH_USE_APPROVED=true 与非空 ANDROIDPLAY_AUTH_AUTHORIZATION_RECORD 后，才准备认证文件。
- 准备时限制文件权限，不打印内容。
- 调用原 LocalMfiAuthenticationClient.load 验证证书格式、P-256、密钥/证书挑战签名匹配；再验证原本地签名调用。临时测试源码不包含任何认证数据。
- 使用授权和再分发授权分开处理。没有 ANDROIDPLAY_AUTH_REDISTRIBUTION_APPROVED=true 时，带认证APK不会被上传到构建artifact；仅保留非敏感报告与校验值。
- 未配置或未记录使用授权时继续无认证源码验证；不会以源码缺文件为由删除或阻塞IPv4修复。

这些变量是项目维护者对已核实授权的记录入口，填写变量本身不是授权证明。必须确认原权利人与允许的用途/范围。

新增工作流通过YAML解析和所有内嵌bash语法检查。真实认证加载检查待获准资源配置后运行，不能代替iPhone信任与PSA实机验证。

补充：AndroidPlayBootstrap会先尝试已有应用私有目录的认证。若同包名、同签名覆盖安装且认证缓存完整，未携带认证资源的APK可能继续使用已有认证；全新安装不具备该条件。当前编译包为debug签名，未核实与原APK签名一致，不能假定能覆盖或保留认证，不能建议为此卸载原版。

最终PSA验收仍未通过：需真实CarPlay画面、照片/视频及对应日志、声音/触摸回归、3轮重连和15分钟持续显示。
