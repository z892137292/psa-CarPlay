# PSA CarPlay 0.2.3 普通单屏配置测试版

基于 DiPlay 0.2.10 的现有 PSA 主干，包名 com.psa.carplay.dev，Android 9 起。

- 在 /info 和 SETUP 两处强制普通单屏配置，即使意外传入副屏配置也不声明 altScreen。
- 不声明增强 UI 请求能力，不提供 videoPlaybackInfo 或启用 videoPlayback。
- 保留 iAPChannel、viewAreas、音频、触摸及 USB/iAP2/NCM/VPN 核心。
- 连接上报名称改为 PSA CarPlay；设备ID、配对身份、认证资产不变。
- 本次不编译或修改独立 PSA Hotspot。

这不是已确认消除 Ultra 提示的正式修复。0.2.8 与 0.2.10 的相关 AirPlay 声明相同，仅凭上游README不能定位提示来源。本版先收紧能力声明供真实车机验证，不任意修改未知功能位或认证证书。若仍出现Ultra，需截图和连接日志继续定位。

安装后建议在 iPhone“设置→通用→CarPlay”忽略旧测试连接，再重新建立连接，排除旧身份记录干扰。先验证授权提示、有线/无线出画面、音乐、触摸。开发签名可能与上一测试APK不同；若提示签名冲突，需要卸载旧开发版并重新配置。
