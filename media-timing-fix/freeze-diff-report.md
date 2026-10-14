# 冻结功能差异报告

比较对象：最新媒体＋IPv4合并版 → 本次恢复时机测试版。不是与初始母包比较。

| 冻结功能 | 修改前后证据 | 结论 |
|---|---|---|
| IPv4 优先 | classes8.dex 完全相同，SHA-256 29a1d9082c4dc5790cdab8cdc5f16bc5d894e1ff6274957dd042615837e424c1 | 既有补丁原样保留 |
| Wi-Fi / 热点 / 蓝牙 | classes8及其他未改DEX逐字节一致；classes3仅两个媒体时机方法变化 | 连接代码未改 |
| USB / MFi / 握手 | 其他DEX、原生库、认证资产完全一致；classes3其余方法一致 | 代码及资产未改 |
| 上一曲 / 下一曲 / 播放暂停 | onMediaButtonEvent、dispatch、各媒体回调、去重、原控制器方法完全一致 | 已修复按键路径保留 |
| Siri / 麦克风 | classes3除两个时机方法外全部一致；其他DEX和原生库一致 | 识别及麦克风代码未改 |
| 视频 / 音频传输及其他功能 | 所有传输方法未改；Manifest、资源、库及其余条目一致 | 未改传输逻辑 |

classes3 的228类、1474方法全部比较。唯一白名单：PsaMediaControl.restoreOnce()V、PsaMediaControl.refreshActive()V。无新增/删除类或方法，类字段和注解相同。完整文本差异见 media-timing.patch；机器检查见 evidence/method-diff.json、evidence/apk-verification.json。

APK签名块重新生成属重新打包必要变化；证书与最新合并版相同。ZIP条目数据一致不表示整个APK二进制一致。
以上证明冻结代码/资产没有被修改；不能据此保证真实车机所有运行行为无回归。焦点恢复时机的行为变化及实车待验项详见主报告。
