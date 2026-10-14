# CarPlay 稳定母包媒体控制定点修复报告

日期：2026-10-14。状态：**已生成独立签名测试 APK，通过构建和静态验证；未安装、未进行 Android ART/PSA 实车验证。**
本报告不宣称方向盘故障已在车辆上修复，不把模拟十轮测试等同于实车十轮验收。

## 1. 输入核验与原包保护

唯一母包：用户附件 `AndroidPlay-1.2.0.apk`，15,378,441 bytes。
SHA-256：`6e5f6c0ab10d16c2abaef6d00eda0e7c0a76d78c7eef55c942e8a0338ce83d5e`。
开始分析前、生成后均核对一致；附件未修改。隔离目录另保留同哈希、只读的母包备份。

| 项目 | 实际结果 |
| --- | --- |
| 包名 | `com.androidplay.app` |
| 版本 | `1.2.0` / versionCode `45` |
| minSdk / targetSdk | 28 / 35 |
| DEX | 11 个；媒体发布器、宿主 Activity 与后台持有者位于 `classes3.dex` |
| 原签名 | v2 验证通过；证书 DN 为 Android Debug |
| 原证书 SHA-256 | `5dc708aa0ae456b490f7b5ce0460e715559ed9be2067f5a9aa8644595daffd41` |
| 原生库 ABI | arm64-v8a、armeabi-v7a、x86_64 |
| 清单 | 已用 aapt 解码检查；包名、权限、组件及所有 Manifest 字节均保持原样 |

使用 Apktool 2.12.1 反汇编全部 DEX，使用 JADX 1.5.3 阅读 `classes3.dex`，以 Smali 为准确依据。
分析阶段 Apktool 曾将资产复制到隔离工作目录，随即删除该独立资产副本；未读取、打印或提交认证私钥内容。
最终构建脚本只解出需修改的 DEX，其他资产在 APK 间原样复制，不再导出认证文件。
没有测试或改变 MFi 认证挑战、私钥、认证实现、原签名或设备授权。

## 2. GitHub 参考核对

- 仓库：https://github.com/z892137292/psa-CarPlay
- 稳定分支 `psa/androidplay-1.2.0-ipv4`：`1cd6ba1ac376de15bcc9ad76b3dd8d8fe932e0e3`。
- 参考分支 `fix/psa-media-return-20261013`：`6bcf6c0520d2529130a3000b9892292122829098`。
- PR #14：https://github.com/z892137292/psa-CarPlay/pull/14；读取时 open、未合并。
- 实际读取 `androidplay-psa/patches/0004-Restore-PSA-media-controls-on-foreground-return.patch`，核对其中的
  `AndroidPlayMediaSession.kt`、`CarPlayHostActivity.kt`、`AndroidPlayMediaButtonReceiver.kt`、`MediaKeyGate.kt`。
- 本次独立分支：`fix/psa-media-mother-20261014`，从参考修复提交分出。未修改 main、稳定分支或 PR #14。

PR #14 报告所引用的旧母包 SHA-256 是 `2b43…7a30`，与本次 `6e5f…3d5e` 不同；仓库另有母包修改报告记录本次哈希。
因此没有拿源码构建 APK 替代本次母包，也没有机械应用源码补丁。参考补丁只用于核对策略。

## 3. 母包真实调用链

以下路径相对于 Apktool 反汇编目录，行号为修改前 Smali 位置。

| 环节 | 实际类/方法及位置 |
| --- | --- |
| 创建系统媒体会话 | `smali_classes3/com/shilapi/xcertplay/CarPlayBackgroundSession.smali`，`store(...)`，917 行起；只有 controller 改变才重建媒体对象 |
| 会话持有者 | 同类静态字段 `owner`、`systemMedia`；`publishNowPlaying(...)` 调用发布器 `update(...)` |
| 媒体元数据发布 | `AndroidPlayMediaSession.smali`，`update$lambda$3(...)`，1014 行起；旧版直接执行 `session.setActive(title.length > 0)` |
| 系统媒体入口 | `AndroidPlayMediaSession$session$1$1` 的 `onPlay/onPause/onSkipToNext/onSkipToPrevious`，分别向原 `mediaCommand` 传入 1/2/4/5 |
| 转发闭包 | `CarPlayBackgroundSession$store$1.smali`，`invoke(I)`，85 行起 → `CarPlayController.sendMedia(I)` |
| 控制器 | `smali_classes4/.../orchestration/CarPlayController.smali`，`sendMedia(I)`，15595 行起；检查 activeSession 与 closed，经原 touchExecutor 排队 |
| 协议发送 | `smali_classes4/.../airplay/AirPlaySession.smali`，`sendMedia(I)`，7678 行起 → `AirPlayHid.mediaReport(I)` → 原 `sendHidReport`；随后发送释放报告 |
| 前后台入口 | `CarPlayHostActivity.smali`，`onPause()` 10770 行、`onResume()` 10789 行；旧版没有媒体控制权恢复调用 |

旧母包应用代码中未找到 `requestAudioFocus`、`abandonAudioFocus`、`OnAudioFocusChangeListener`。
标准媒体按键事件由系统 MediaSession 默认回调行为转成上述命令；原包没有专门的应用级媒体按键接收器或 Activity 按键拦截。
搜索全部 Smali 的媒体按键、dispatchKeyEvent/onKeyDown/onKeyUp、MCU/CANBUS 等入口，命中按键分发的仅为 AndroidX 框架支持代码。
原生桥接声明指向热点查询和 I2C 通道，没有识别出独立的 PSA 方向盘媒体输入桥。

**这只说明 APK 内未发现该入口，并不证明 PSA 系统/MCU 不存在私有通道。** 未逆向车机系统服务或猜测厂商广播。
若 PSA 方向盘事件绕过 Android 标准媒体会话，仍可能需要另外的设备侧定位；当前包不保证覆盖该路径。

## 4. 确认的缺口和本次改动

静态确认：旧版元数据刷新会无条件重激活会话；没有失焦让出状态；原 Activity 返回时没有明确恢复入口。
这与描述的故障相符，但车辆上实际失效是否完全由此造成，尚未通过日志证明。

仅修改 3 个既有类的 6 个方法：

1. `AndroidPlayMediaSession.<init>`：将原回调交给新增 `PsaMediaControl` 包装，声明标准媒体按键/传输控制能力。
2. `AndroidPlayMediaSession.update$lambda$3`：在原 revision 检查之后，把标题是否非空及 playing 状态交给控制权门控，取代直接激活。
3. `AndroidPlayMediaSession.close`：关闭门控、释放已持有的焦点；原资源释放逻辑保留。
4. `CarPlayHostActivity.onPause`：记录当前 Activity 已离开前台，并通知当前会话。
5. `CarPlayHostActivity.onResume`：在原 super 调用后记录前台状态，并通知当前会话。
6. `CarPlayBackgroundSession.store`：设置 owner 后同步新 owner 的实际前台标记，覆盖“会话创建晚于 onResume”及同控制器 Activity 接管场景。

新增两个桥接方法、两个字段以及 `PsaMediaControl` 与其 Runnable 内部类。新增辅助代码使用 API 28 编译、D8 min-api 28。
原有回调及 `CarPlayController`、`AirPlaySession`、HID 编码均不修改。

控制规则：

- 首次/返回前台时，有标题或正在播放才尝试一次焦点申请；仅系统授权后激活会话。
- 已持有焦点时重复 onResume 不重复申请；后台退出取消尚未消耗的申请机会。
- 申请拒绝/异常后保持停用；元数据、按键及定时器不会触发重试，需新的前台转换。
- 永久失焦立即停用会话并放弃焦点；后续更新和迟到的 GAIN 不会夺回控制权。
- 临时失焦/duck 停用会话并等待系统 GAIN；返回前台也不重复申请，避免抢走临时音频所有者的控制权。
- 正在播放时，失焦通过原控制器发送一次暂停音乐命令；不会修改音频传输或强制切换音频路由。
- GAIN 恢复控制能力，不自动发送播放命令；因此暂时失焦后的音乐可能需要用户继续播放。
- 仅因 Activity 在后台不释放已持有的正常媒体控制，保留 CarPlay 后台播放/连接；真正失焦才让出。
- 所有前台通知排入原主线程 Handler，门控方法同步；关闭后丢弃迟到通知和命令。
- 按键 85/87/88/126/127 复用原 1/2/4/5 命令；过滤 UP 和 repeat，以 key/downTime/device 三元组保留最近 32 次去重。
- 已处理按键不再调用默认 `super.onMediaButtonEvent`，避免标准事件的二次分发。
- 原 seek 与 stop/disconnect 入口保留；失焦禁止 seek，明确 stop 仍能断开。

与 PR #14 的适配差异：

- 没有新增 `AndroidPlayMediaButtonReceiver` 或 Manifest 组件。使用存活的原 MediaSession 直接接收按键，不让按键冷启动连接。
- 清单与资源字节不变，仅替换一个 DEX；避免为接收器重新编译 Manifest/resources。
- 临时失焦不会因前台返回重申焦点，已持有焦点也不重复申请。
- 通过原暂停命令实际通知手机让出音乐；不会在焦点恢复时自动播放。
- 去重使用小容量历史，能覆盖交错重复事件。若厂商另外同时注入无时间标识的 transport 回调，则无法仅凭标准回调保证跨通道去重。

没有修改 USB、MFi、Wi-Fi、蓝牙、视频解码、麦克风、连接协议、网络参数或音频路由代码。

## 5. 构建、签名和验证

产物：`AndroidPlay-1.2.0-media-fix-test.apk`，15,366,494 bytes。
SHA-256：`079c85404f7719099af22f3cc15565c8cf83a0648c071f6aa8326c8e68281dc6`。

| 检查 | 结果/范围 |
| --- | --- |
| 母包 SHA-256 与备份 | PASS，前后相同 |
| ZIP CRC、重名及条目集合 | PASS，122 个条目无增删 |
| 逐条目内容比较 | 仅 `classes3.dex` 改变；其余 121 个逐字节一致 |
| Manifest、resources、res、原生库和认证资产 | 全部字节一致；未输出认证内容 |
| 原有方法差异 | `classes3.dex` 原 226 类/1450 方法中仅 6 方法改变；其余 1444 方法反汇编完全一致；无原方法删除 |
| 新增内容 | 2 个辅助类；2 个原类桥接方法；2 个字段 |
| 全部 11 个 DEX | 魔数、长度、表边界、SHA-1/Adler32 校验通过；原包全部已反汇编，修改 DEX 再反汇编通过 |
| 新增 Java API 兼容性 | 用 API 28 android.jar 编译及 D8 min-api 28 转换通过 |
| APK 签名 | v3/API 28 验证通过；v2 在显式校验范围 24–27 下也验证通过（仅检查签名，不代表本包支持低于 minSdk 28） |
| 对齐 | zipalign `-P 16 -c 4` 通过 |
| 清单与 badging 输出 | 与母包一致 |
| 完整补丁复现 | 从原始 DEX 零模糊应用 `media-fix.patch`；同工具同测试密钥两次构建最终 APK 字节一致 |
| 控制逻辑测试 | 17 场景、86 断言通过，包括模拟十轮切换；测试运行实际辅助 Java 类，Android API 由主机替身提供 |
| Android/ART 加载、安装、启动 | 未执行，无连接设备/模拟器 |
| 方向盘/OEM/导航/无线连接实车测试 | 未执行 |

v2 诊断命令限制在 Android 7/8 校验范围，会提示其不了解 v3 scheme；API 28 的 v3 校验正常通过。
JADX 能保存修改后的辅助类；部分同步方法以 fallback 指令形式呈现，未将该反编译文本重新编译回 APK。
第一次签名调用因同一单行口令文件被重复读取而失败，修正为 PKCS12 共用口令后重新完整构建成功；失败产物未交付。

新签名证书：`CN=PSA Media Fix Independent Test 20261014,O=Private Testing,C=CN`。
新证书 SHA-256：`9c7d3e50d56195ce9932ab47fe740f2ceb0d210d98a737cceda124205cc6efe9`。
使用独立生成的 RSA 3072 测试密钥；没有原签名私钥、没有冒用原签名。测试密钥未进入交付源码或 Git。

**包名相同但证书不同，正常 Android 安装规则不允许直接覆盖原版。** 不提供卸载原版、清除数据或绕过签名校验指令。
当前未执行安装，不涉及车机数据变化。可以在没有同包名已安装应用的隔离测试设备上安排验证；主车机需先完成可靠的数据保护决策。
Android 多用户不能被当作绕过同包名签名冲突的方案；改包名也不属于本次修复。

认证资产字节不变不等于已证明重新签名后 iPhone/MFi/设备策略兼容。本次未运行认证挑战或实车握手。
如果运行发现签名绑定、系统签名权限或认证限制，应停止对应安装/连接尝试并记录具体错误，不修改认证实现来绕过。

## 6. 实车验收清单（全部待验证）

仅在测试环境具备合法安装条件、原版和数据均可恢复后进行，不以本报告作为卸载原版的指令。

| 场景 | 检查 | 当前状态 |
| --- | --- | --- |
| 首次连接 | 上一曲/下一曲/播放/暂停各一次，手机各响应一次 | 待实车 |
| CarPlay → 原车音乐 | 原车按键正常；CarPlay 会话停用，元数据刷新不重夺焦点 | 待实车 |
| 原车音乐 → CarPlay | 明确返回 CarPlay 后只出现一次恢复尝试，按键目标正确 | 待实车 |
| 连续 10 轮 | 每轮记录按键目标、焦点状态、单次响应；没有丢控制或循环争抢 | 仅主机模拟通过，待实车 |
| 导航与临时焦点 | 通话/导航时不会抢占；结束后控制恢复，记录音乐是否需手动续播 | 待实车 |
| 后台、音频、无线 | 后台连接持续、音频正常、热点/无线连接无退化 | 待实车 |
| 原包与回退 | 母包哈希匹配，可用且经过验证的数据恢复路径 | 母包保留；数据恢复未验证 |

每个切换点采集只读证据：

```sh
adb shell dumpsys media_session > media-session.txt
adb shell dumpsys audio > audio-focus.txt
adb logcat -d -v threadtime -s PSA-MEDIA:I '*:S' > media-fix-log.txt
```

权限拒绝时保留错误，不绕过系统限制。日志的 `dispatch` 只证明调用了原手机命令入口；`phoneAck=unknown` 不代表手机实际响应。
若日志完全没有方向盘 `key`/transport 回调，但原车有反应，需要设备侧定位厂商输入路径；不要继续盲目抢焦点。
观察到周期性抢占、重复按键、连接/导航退化或认证错误时，停止测试并按 `rollback.md` 处理。

## 7. 交付与限制

- 测试 APK：已构建、私下交付，不上传公开 GitHub。
- `media-fix.patch`：完整、可独立复现的 Smali 补丁。
- `media-fix-report.md`：本报告。
- `sha256.txt`：唯一母包和测试包校验值。
- `rollback.md`：安装限制、数据保护和回退方案。
- `media-fix-reproducible-source.zip`：可读辅助源码、补丁、脚本、主机测试及证据。无完整 APK、认证文件或签名私钥。

最终技术状态是“可交付的定点修复测试候选包”，不是“已在 PSA 车机验收的稳定发布版”。
