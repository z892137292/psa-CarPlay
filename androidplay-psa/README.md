# AndroidPlay 1.2.0-psa01 / Build 46

PSA Android 9 / API28 / 1920×720 的独立 IPv4 兼容试验，不覆盖本仓库原 DiPlay 分支与版本。

原项目 Roylyl/AndroidPlay，固定基线 793e488334a4e0c23459b659c271b7715ae9a9e7。
按顺序应用 patches/ 中两个提交：网络与显示诊断、热点界面三处微调。系统热点仍由用户开启；复用原检查、系统设置跳转、返回继续及断开处理。未重写协议栈或解码器。

运行 build-androidplay-psa.yml。产物保留在 Actions artifact，不发布或覆盖已有 Releases。
没有明确配置运行时认证时，文件名含 SOURCE-ONLY / NO-CARPLAY-AUTH，**不能用来验证 iPhone CarPlay 连接**。认证由本仓库明确配置的 ANDROIDPLAY_MFI_IDENTITY_PK8_BASE64 与 ANDROIDPLAY_MFI_CERTIFICATE_P7B_BASE64 Secrets 提供；工作流不会从 DiPlay APK 提取身份。认证文件只在临时运行环境内准备，不提交源码仓库。不得把认证资料发到公开 Issue、源码或日志。

本流水线使用 debug 签名，不能保证覆盖已安装 APK；保留原 APK 和设置，签名不兼容不要直接卸载。APK 包名为 com.androidplay.app，minSdk28，测试版本 code46。SHA-256、测试与 Lint 结果在构建产物内。

源码地址策略的 7 项独立 JVM 测试已通过，完整 Android 构建结果以 Actions 为准。测试或 Lint 失败时仍可保存诊断 APK，但最终 job 标记失败，不把编译成功当成项目通过。

PSA 真机待验收：手动开热点 → ap0 IPv4 listener/Bonjour/iAP2 地址一致 → RFCOMM/MFi → AirPlay TCP/session → 视频 SETUP → H.264 解码/Surface → 实际可见 CarPlay。
必须有物理屏幕照片或视频与相应日志；检查音频、触摸、至少3轮重连、连续15分钟并切换界面，不黑屏、不闪退、不返回Launcher。first frame rendered 和 Texture 更新均不足以替代真实屏幕验收。

回滚使用原成功 APK/签名与源码基线。本试验不改 Launcher，不提交原始设备日志或 OEM APK。
