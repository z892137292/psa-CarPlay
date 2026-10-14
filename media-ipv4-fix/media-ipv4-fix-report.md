# AndroidPlay 1.2.0：媒体控制 + IPv4 优先合并测试版

日期：2026-10-14。已重建并完成静态验证，未进行 Android 安装/ART 或 PSA 实车验证。

## 本次合入

用户要求在此前媒体控制修复基础上补回 IPv4 优先，以适配 PSA Android 9 手动热点连接。

- 输入唯一母包 SHA-256：`6e5f6c0ab10d16c2abaef6d00eda0e7c0a76d78c7eef55c942e8a0338ce83d5e`。附件和只读备份未修改。
- 包名 `com.androidplay.app`，版本 `1.2.0` / 45，minSdk 28、targetSdk 35 保持原值。
- `classes3.dex`：此前媒体控制修复保留，SHA-256 与已交付媒体单项包的该 DEX 完全相同。
- `classes8.dex`：在 `ManualHotspotManager.hotspotAddress(NetworkInterface)` 将地址选择转给新增 `WirelessHostAddressKt.psaHostAddress(List,int,NetworkInterface)`。

只在 **Android 9 / API 28，且接口名为 ap0** 时，从该接口真实地址列表优先选择有效 IPv4。
过滤 loopback、link-local、any-local、multicast；无有效 IPv4 时调用原 `wirelessHostAddress`。
其他系统版本及其他接口继续原逻辑。不写死 IP，不创建热点，不改变认证或连接协议。
这恢复的是既有 PSA/ap0 定向补丁；如果实际接口不同，不能据此保证连接成功。

补丁源自同仓库 `androidplay-apk-patch/psa-mother-apk.patch` 中两个 `smali_classes8` 文件片段，原样提取。
没有混入该旧补丁中的首页摘要、密码显示或其他 UI 改动。原 `wirelessHostAddress` 方法完整保留。
合并补丁 `media-ipv4-fix.patch` 可直接从原母包复现两项修复；`ipv4-only.patch` 便于审查本次增量。

## 检查结果

| 检查 | 结果 |
| --- | --- |
| 原母包 SHA-256 | 与指定值一致，原件不变 |
| ZIP 条目 | 122 个，无增删；仅 classes3.dex、classes8.dex 内容改变 |
| 其他条目 | 120 个逐字节一致，包括 Manifest、资源、原生库和认证资产 |
| 全部 11 个 DEX | 长度、表边界、SHA-1、Adler32 通过 |
| 改动 DEX 再反汇编 | 通过 |
| 逐方法差异 | 媒体 6 个原方法 + 网络 1 个原方法；无原方法删除；新增原类方法共 3 个、辅助类 2 个 |
| 媒体补丁一致性 | classes3.dex 与前次已交付媒体修复 DEX 字节一致 |
| 媒体主机测试 | 本次重新执行，17 场景、86 断言通过；包含模拟 10 轮切换 |
| APK 签名 | 独立测试签名，API 28 的 v3 验证通过 |
| zipalign | 16 KiB 原生库对齐、4 字节条目对齐检查通过 |
| Manifest/badging | 与母包一致 |
| Android/ART、安装、PSA 连接与方向盘 | 未执行，待真实设备验证 |

本次 IPv4 逻辑通过原补丁精确应用、DEX 汇编/反汇编及方法差异验证；没有把静态检查称为实际联网测试。
媒体主机测试使用模拟 Android API，不等于车辆媒体控制验收。不得保证本包已解决所有连接问题。

## 产物及签名

- 文件：`AndroidPlay-1.2.0-media-ipv4-fix-test.apk`
- 大小：15366494 bytes
- SHA-256：`968c4c2bf8aa9187ae4cd619cb59c4eaf1e4792f0ba002d773cebdf38ca2c311`
- 本次测试证书 SHA-256：`b2377f958e32a9a7ba4a4c8357614206297de66e745b10edfa01956ec826a526`
- 原母包证书 SHA-256：`5dc708aa0ae456b490f7b5ce0460e715559ed9be2067f5a9aa8644595daffd41`

前次中断后临时工作目录被清理，尚未保存的合并 APK 和旧测试私钥丢失。本次从已提交源码、原母包重建，并使用新生成的独立测试签名。
因此本文件哈希不同于中断前临时构建记录；应以本报告与本次 sha256 文件为准。
当前证书也不同于前次媒体单项测试包的 `9c7d3e50d56195ce9932ab47fe740f2ceb0d210d98a737cceda124205cc6efe9`。
**不能直接覆盖原版，也不能直接覆盖先前测试签名的安装。不要为试包卸载原版或清除数据。**
测试密钥没有公开上传；没有修改、冒用或绕过原签名。认证资源只在 APK 间原样复制，未导出/公开密钥。

## 实车待验收

在具备安装条件的独立测试设备上，先确认 Android 版本、热点接口名和实际 IPv4；查看连接日志是否使用了接口 IPv4。
依次验证首次连接、CarPlay→原车音乐→CarPlay、上一曲/下一曲/播放暂停、10 轮切换、后台连接、导航和音频。
母包未改动不代表重新签名的包已通过 iPhone/车机认证兼容测试。遇到签名、认证或设备权限阻碍，停止相应操作并记录错误，不改认证逻辑绕过。
回退和数据保护见 `rollback-media-ipv4.md`。完整 APK 不上传公开 GitHub；源码/补丁/报告仅提交独立修复分支，保留 PR #14。
