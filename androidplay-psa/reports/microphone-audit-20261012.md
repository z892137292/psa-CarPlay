# PSA AndroidPlay 1.2.0 麦克风定点审计

日期：2026-10-12。上游固定为 Roylyl/AndroidPlay `793e488334a4e0c23459b659c271b7715ae9a9e7`。工作分支：`fix/psa120-microphone-state-20261012`。未合并，未安装或覆盖车机稳定 APK。

## 结论与证据边界

已确认应用层缺陷：原程序仅依赖 `startRecording()` 未抛异常便报告启动、启动读取线程。Android 9 的实现仅在 native_start 成功时更新 recordingState；native start 失败可正常返回而仍保持 STOPPED。因此必须检查 recordingState==3。这项修复消除误报，不能把它解释为已经恢复麦克风输入。

现有日志显示输入从内置麦克风路径转到 Telephony RX，并出现受保护捕获权限拒绝。这证明底层选择了异常输入路径，尚不能确定是厂商 Audio Policy 的设备选择、系统音频模式/并发录音状态，还是 MediaTek HAL 的内部限制。没有依据宣称“HAL 已修复”，也没有授予 CAPTURE_AUDIO_OUTPUT。

| 项目 | 现有证据 |
|---|---|
| 当前请求设备 | 用户截图选择“系统默认设备”；截图不能证明实际 route，也不能证明每段旧日志使用同一设置 |
| 请求 AudioSource | telephony→VOICE_COMMUNICATION(7)，speechrecognition→VOICE_RECOGNITION(6)，其他→MIC(1) |
| 实际底层路径 | 日志含 0x80000004 内置麦克风，随后 0x80000040 Telephony RX，HAL 参数为 16 kHz |
| 失败位置 | getInputForAttr 权限拒绝、native AudioRecord restore/start -22、Java read -2 |
| 上行证据 | 历史成功文字与失败同时出现；没有首包成功日志，不能证明收到有效声音 |
| Siri/ChatGPT/微信对应关系 | 未标记的 speechrecognition 会话不能唯一归属某个 iPhone 应用；需实车标记 |

`voice_full.txt` 的 12:02:17 会话：请求 speechrecognition/48000 Hz；HAL 先开内置麦克风，再开 Telephony RX；CAPTURE_AUDIO_OUTPUT denied；start -22；紧接着 uplink started；read -2。文件中有 20 次 start -22、20 次启动文字、20 次 read -2，无首包日志。`01_idle.txt` 只作为空闲环境对照，不能代表失败瞬间的政策状态。

新增 `carplay_audio_test.log`：19 次 start -22、19 次启动文字、19 次 read -2，无首包日志。17:05:05 的 telephony 会话进一步复现同一问题：

| 日志行（按 LF 换行） | 事件 |
|---|---|
| 479768 | 17:05:05.072，HAL openInputStream 内置麦克风 0x80000004 / 16000 Hz |
| 480119 | 17:05:05.105，HAL openInputStream Telephony RX 0x80000040 / 16000 Hz |
| 481649 | 17:05:05.107，CAPTURE_AUDIO_OUTPUT 要求 |
| 483240 | 17:05:05.108，AudioRecord start -22 |
| 483260 | 17:05:05.110，应用错误报告 telephony uplink started |
| 483439 | 17:05:05.118，read -2 |

日志缓冲区可能交错，应按时间戳和 PID 关联，不能仅按相邻行认定同一输入实例。HAL 的 16 kHz 参数也不等于 Java 48000 Hz 请求非法；framework 可做转换，不能据此擅自改采样率。

## Android 9 机制核对

核对了 AOSP android-9.0.0_r1：

- [AudioRecord.java](https://android.googlesource.com/platform/frameworks/base/+/android-9.0.0_r1/media/java/android/media/AudioRecord.java)，startRecording 第 980–992 行，仅 native_start==SUCCESS 才设置 RECORDSTATE_RECORDING。
- [AudioPolicyInterfaceImpl.cpp](https://android.googlesource.com/platform/frameworks/av/+/android-9.0.0_r1/services/audiopolicy/service/AudioPolicyInterfaceImpl.cpp)，getInputForAttr 的 API_INPUT_TELEPHONY_RX 与 MIX_CAPTURE 进入 captureAudioOutputAllowed 检查。该权限不是普通 RECORD_AUDIO 的替代。

这是 AOSP 机制对照，不是 PSA 厂商 Policy/HAL 的源码证明。Root/SELinux Permissive 不能自动消除 framework Binder 权限检查。不能从当前资料推断拒绝只是缺少普通麦克风授权。

## 最小补丁

原 0001、0002、0003、0004 已在固定 commit 上 clean git am，未混入旧测试补丁。0004 保持原文件；新增 0005 只补充麦克风诊断、失败状态测试和自愿音源对比。0005 在仅应用前四个补丁的干净 worktree 上 git apply --check 通过。

修改范围：MicrophoneUplink、输入源/状态辅助函数与测试、AndroidMediaSink 的输入配置传递、CarPlaySettings 的 audio_input_source 和声音页测试选项。另外删除 OpusEncoder 原日志中的编码数据前 16 字节，仅保留长度；编码行为不变。没有修改包格式、加密、编码算法、投屏、网络、热点或视频链路。

- 创建前记录请求 source、设备 type/id/address 和格式，避免创建失败丢失请求证据。
- preferredDevice 的返回只代表偏好是否接受；实际使用设备以 routedDevice 为准。设置偏好的异常纳入清理路径。
- start 后检查 recordingState；失败时关闭本会话 recorder/socket/encoder，返回 false；不会进入成功文字或读取线程。
- read 记录返回值，负数保留原退出清理逻辑；没有新增无限重试或自动换源。
- 每秒最多一次读取驱动的统计，并在首次读取、失败、结束时输出。pcmFrames 为每通道采样帧数，frameCount 为完成的输入块数；packetSend 仅在 socket.send 正常返回后累加，不能代表手机收到或语音有效。read 阻塞时不会凭空生成进度。
- 记录 recordingState 与 routedDevice；null 显示 unavailable，不认定成功。
- 删除原上行首包字节头和 Opus 编码数据字节头输出，仅记录长度和计数；不新增声音、PCM、网络内容、账号或密钥日志。
- auto 是默认且保持原映射。手动 mic / speechrecognition / voicecommunication 只对下一次创建的语音会话生效，不切换正在进行的 recorder，也不自动回退。

已有恢复行为仍由 Android AudioRecord native restore 完成；Java 层在负数读取后退出，未新增 HAL 重置。状态检查修复启动误报，读取失败仍需单独观察。

## 实车验收与回滚

先保留原 APK 和安装状态。本次 source-only APK 与稳定程序同包名，不能用 adb install -r 覆盖稳定 1.2.0。它不包含项目要求的本地认证输入，不能作为完整 CarPlay 连接验收包。需要由持有合法原运行环境的构建端完成匹配基线的实车测试构建；本任务不读取、提取或改动认证材料。

每次仅启动一个语音场景，清楚标记日期、手机应用、音源选项、输入设备选项、是否说话。保存同一时间轴：

```sh
adb logcat -v epoch -s xcertplay-usb AudioRecord AudioFlinger AudioPolicy AudioPolicyIntefaceImpl
adb shell /system/xbin/su 0 dumpsys audio
adb shell /system/xbin/su 0 dumpsys media.audio_flinger
adb shell /system/xbin/su 0 dumpsys media.audio_policy
```

先采空闲快照；连接 CarPlay；依次 Siri、ChatGPT、微信，每次讲话 10 秒、结束该会话；在启动、说话、结束时分别取 dumpsys 快照。首次保持 auto 和系统默认设备。然后分别选择 speechrecognition、mic、voicecommunication，关闭上一次语音会话后重新打开，重复三种应用并记录实际 requestedSource，不能凭 UI 值假定已经生效。

验收要求：创建 initialized、启动 recordingState=3；routedDevice 与同时间 policy 输入一致且为有效麦克风路径；readResult 持续正数、pcmFrames/frameCount 增长、packetSend 增长；iPhone 端实际识别讲话。同时确认音乐、投屏保持正常。任何一个计数不能单独证明麦克风有效。若 start 失败，应看到 recording failed 和停止状态，不能看到同一会话启动成功；若 read 失败应停止并清理。

只有某源在三种应用中都通过真实讲话验收，才能推荐该源；目前没有这份数据，不改默认。若三源都失败，也不猜 HAL 故障原因。

配置回滚：选择 auto，结束并重新创建语音会话。代码回滚：撤销 0005，保留 0001–0004；0004 仅检查启动状态。若独立测试环境安装了匹配认证且签名不同的程序，回滚必须按原构建端安装方案恢复保存的原 APK，不能以卸载稳定程序为本报告的默认步骤。

## 尚缺证据

缺少补丁版真实 requestedSource/recordingState/routedDevice/read/packet 日志；失败同一秒的 dumpsys audio、audio_flinger、audio_policy；有应用/音源标签的 Siri 成功与 ChatGPT/微信失败对照；PSA 厂商实际 Audio Policy 配置及对应 HAL 行为依据。稳定 APK 带软件 Opus 回退日志，而固定上游源码的 OpusEncoder 没有这段回退，当前任务没有更改编码器，不能宣称源码测试包完整复现稳定 APK 的运行能力。

构建结果另见 build-microphone-20261012.md。实车功能状态：未验证；路由根因归属：尚未判定。
