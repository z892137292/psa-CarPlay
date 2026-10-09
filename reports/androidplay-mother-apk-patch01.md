# AndroidPlay PSA 母包定点修改版 apkpatch01
日期：2026-10-09。范围：用户本人自有 PSA Android9 车机的非商业测试；不公开发布带认证 APK。未重新执行完整 Gradle 构建。

## 母包与产物
母包 AndroidPlay-1.2.0(1).apk SHA-256：6e5f6c0ab10d16c2abaef6d00eda0e7c0a76d78c7eef55c942e8a0338ce83d5e。
产物 AndroidPlay-1.2.0-B45-PSA-apkpatch01.apk，15,346,213 bytes。
产物 SHA-256：c8add5920c96fbbf3cc35b3273e856cc44d3b4288169b1fc3c26096499c98536。
包名 com.androidplay.app；版本 1.2.0 / versionCode45（保留母包标识，以文件名区分补丁版）；minSdk28；targetSdk35。原生库 arm64-v8a / armeabi-v7a / x86_64 保持母包原字节。

## 工具与修改
Apktool2.12.1 反汇编/Smali封装；Androguard4.1.4解析/对照；uber-apk-signer1.3.0 zipalign/签名验证。
分析副本不含认证和原生库文件；最终包以母包 ZIP 条目为基准，认证条目从母包直接在内存中保留，没有导出独立认证文件。
只替换 classes3.dex 和 classes8.dex。3个原方法改变：
1. ManualHotspotManager.hotspotAddress：改为调用限定接口的地址选择辅助方法。
2. AndroidPlayActivity.render：增加首页热点摘要与断开入口。
3. AndroidPlayActivity.editHotspot：将原密码输入框放入水平容器并加入显示按钮。
新增 WirelessHostAddressKt.psaHostAddress、PsaPasswordToggle、PsaHomeSummary。
API28/ap0优先有效实际IPv4，排除loopback/link-local/any-local/multicast；无IPv4回退原wirelessHostAddress。其他接口/系统继续原选择逻辑，未硬编码车机IPv4。
默认隐藏密码，按钮切换并保留选区；原EditText仍交给原保存/验证回调。首页仅显示SSID与密码配置状态；母包没有可靠来源记录，因此不编造自动/手动来源。
断开按钮使用现有 ExternalSyntheticLambda32 -> renderSettingsPage$lambda$67 -> resetWifi。原会话断开方法及手动热点流程未改。
原认证协议、RFCOMM、iAP2、AirPlay、USB、MediaCodec、Surface、Activity生命周期、音频和触摸代码未修改。

## 最终 APK 验证
- ZIP完整性：PASS。
- AndroidManifest.xml/resources.arsc/res/原生库/认证资源及其余DEX：逐字节保持母包；92个非修改非签名条目比对PASS。
- 两份认证资源：identity.pk8 67 bytes，certificate.p7b 607 bytes；非空且与母包完全一致，PASS。无认证私钥内容输出、无独立密钥上传、无密钥提交。
- 全部11个DEX：解析、SHA1和Adler32校验PASS。
- 两个修改DEX：逐方法解码指令对照，仅上述3个原方法不同，未删除原方法；其他原方法指令/访问标志一致。
- 本地认证：原LocalMfiAuthenticationClient加载/签名逻辑与LocalMfiProbe进行2轮启动各3次签名，64字节结果、证书匹配、改变挑战拒绝均PASS。仅测试输入层适配ZIP内存流，未将该适配写入APK，也未导出凭据。另用Python内存验证P256匹配通过。
- zipalign PASS；Android签名v2/v3验证PASS。
- 新增调用均采用API28已有API；DEX静态结构验证通过。没有Android9运行设备/ART验证器，实际安装启动与运行时DEX加载仍须实机验证；不能把DEX解析成功等同于ART验收。

## 签名与安装
母包签名证书SHA256：5dc708aa0ae456b490f7b5ce0460e715559ed9be2067f5a9aa8644595daffd41。
补丁包签名证书SHA256：9aee4f702cac2e51ac7473604ac885ed924b2fda6f9b494a7eec2eb0252143d6。
使用当前私有环境生成的独立PSA测试签名，未公开签名私钥。签名不同，不能正常直接覆盖安装旧版。不得绕过签名检查；本次没有要求用户卸载，也没有修改车机数据。
安装前保存原APK，并完成应用数据完整备份（普通系统备份可能不含noBackupFilesDir中的认证缓存）。备份未确认前不要卸载或清除数据。后续是否换装由用户在确认备份后决定。
回滚使用已保留母包和已验证的应用数据备份；两个签名不同，回滚同样不能假定可直接覆盖。修改记录可撤回，不影响既有源码PSA分支。

## 使用范围与许可记录
用户明确授权个人母包定点修改与私有交付。本次保留已有条目，没有取得或宣称第三方认证资源的新增授权；上游固件来源/再分发许可不确定性仍保留记录。非商业用途不是普遍授权证明。该APK不上传公开GitHub/Release/Actions；公开仓库仅保存不含认证资源的修改记录。
本次不再将未确认事项混为源码许可，也不重复要求联系原作者或提供Apple授权文件。不得将本产物推广为官方认证/商用发行版。

## 真机验收：未测试 / 未通过
此包具备通过本地加载验证的母包认证资源，但尚未确认本次补丁包被iPhone接受或PSA真实显示CarPlay。
用户手动开系统热点，核对ap0实际IPv4；记录RFCOMM→iAP2/MFi→AirPlay TCP/Session→视频SETUP→解码→Surface→实际屏幕。
检查三处UI、实际画面、切后台/回前台、异常回Launcher、音频触摸；3轮断开重连、至少15分钟显示；提供对应日志和照片/视频。首帧日志不能替代画面证据。
本次未凭无黑屏证据修改解码/渲染逻辑。
