# 麦克风补丁编译与 APK 校验

日期：2026-10-12。分支 `fix/psa120-microphone-state-20261012`，未合并。固定上游 `793e488334a4e0c23459b659c271b7715ae9a9e7`。

## 应用和检查结果

在干净固定源码上依次 git am 原 0001、0002、0003、0004，全部成功。没有引入旧测试补丁。原四补丁单独在干净 worktree 完成所有检查；新增 0005 在该 worktree 上 git apply --check 成功，最终源码 git diff --check 成功。

| 检查 | 仅原 0001–0004 | 加入最终 0005 |
|---|---|---|
| shared:testDebugUnitTest | 205 项，通过 | 209 项，通过 |
| common:testDebugUnitTest | 57 项，通过 | 57 项，通过 |
| mobile:lintDebug | 通过，0 错误、5 警告 | 通过，0 错误、6 警告 |
| mobile:assembleDebug | 通过 | 通过 |
| 综合构建 | BUILD SUCCESSFUL，3m22s | BUILD SUCCESSFUL，4m15s |

新增 4 项测试验证原音源映射保留、显式配置映射、native 启动失败但不抛异常时必须拒绝成功状态、真实录音状态成功以及异常传播。这些是代码状态控制测试，不是车机 AudioRecord 或 HAL 实测。

最终 lint 的六项为 OldTargetApi、GradleDependency、两项 TrustAllX509TrustManager、UnusedResources、UseTomlInstead。额外的 GradleDependency 是未改动的 androidx.activity 依赖更新提示，随依赖元数据可见性出现；没有麦克风源文件的 lint 错误或警告。TLS 信任检查警告属于原代码，本任务没有修改认证或网络逻辑。

## 构建环境与复现

Temurin JDK 25.0.1+8、Gradle 9.7.1（与项目 wrapper 完全相同版本）、AGP 9.4.1、Kotlin 2.2.10、Android SDK android-37.0、Build Tools 36.0.0、NDK 29.0.14206865。

实际使用预下载的 Gradle 9.7.1 可执行文件，执行与 wrapper 下列任务等价的构建。由于不能读取或提供认证材料，显式使用已有 sourceOnly 开关，没有修改认证检查来绕过要求。

```sh
git clone https://github.com/Roylyl/AndroidPlay.git upstream
git -C upstream checkout --detach 793e488334a4e0c23459b659c271b7715ae9a9e7
# 配置 git 提交身份后，按序应用 psa-CarPlay 测试分支的补丁
git -C upstream am /absolute/path/to/psa-CarPlay/androidplay-psa/patches/000*.patch
cd upstream
./gradlew -Pandroidplay.sourceOnly=true :shared:testDebugUnitTest
./gradlew -Pandroidplay.sourceOnly=true :common:testDebugUnitTest
./gradlew -Pandroidplay.sourceOnly=true :mobile:lintDebug
./gradlew -Pandroidplay.sourceOnly=true :mobile:assembleDebug
```

本环境额外用临时 init script 向 Test JVM 传递网络代理并把 Robolectric Maven 仓库设为 repo.maven.apache.org；没有修改项目依赖或测试。最终构建采用 in-process Kotlin 编译、max-workers=2、no-configuration-cache。早期失败包括损坏 JDK 下载、代理设置、并行构建缓存锁和 Robolectric 无法联网，均为环境问题；最终结果以以上两次 BUILD SUCCESSFUL 为准。没有隐藏或跳过失败测试。

现有 `.github/workflows/build-androidplay-psa.yml` 已按 `patches/*.patch` 顺序应用补丁，包含测试、lint、源码构建和独立认证构建检查。本任务没有修改或触发认证构建；测试分支提交不会自动触发仅匹配基线分支的 push 事件。GitHub Actions 结果尚未验证，以上结果是本地真实构建结果。

## APK SHA256

原四补丁 source-only APK：

```text
c6b4c458c5df031a19bf900e7db81df07d71b67c74658a569efd628316ca17b5
```

最终 `AndroidPlay-1.2.0-microphone-source-only.apk`：

```text
8a8e7cec5ffb0a0a4a77da005fdcf9df74d10ae403dab201b717fb7eeaedb589
```

## 包结构与 Android 9 静态兼容检查

- 包名 com.androidplay.app；versionCode 46；versionName 1.2.0-psa01。
- minSdk 28，targetSdk 35；RECORD_AUDIO 权限存在。
- apksigner verify --min-sdk-version 28 成功，v2 签名有效，单一 debug signer；没有使用或修改稳定 APK 的签名。
- ZIP CRC 完整性检查成功；DEX 包含新增 MicrophoneInputSource、requestedSource/sourceChoice/packetSend 诊断代码。
- 包含 arm64-v8a 原生库 liblocal_hotspot_radio.so、libxcertplay_i2c.so；本任务未更改它们。
- 最终编译的 OpusEncoder.class 不含被删除的 head= 日志内容；不记录编码声音字节。
- assets/offline-mfi 文件数量为 0；此包仅用于源码验证，不具备已验证的完整 CarPlay 连接能力。

静态检查不能替代 Android 9 实机启动、录音、路由和语音识别验收。没有连接车机，没有安装 APK，没有修改系统路由。

稳定 CarPlay-1.2.0.apk 的 SHA256 仍为：

```text
2b43c7b412271b137d3eeaddf9f5a97e2bcb94f3df525ea01b88585d0b507a30
```

**不要对稳定车机执行 adb install -r 安装本 source-only 包。** 它使用相同包名，不能作为保留稳定安装的并行测试应用。完整连接测试包需要合法原运行环境的构建端提供匹配基线，认证输入和稳定软件 Opus 回退差异见 [审计与实车步骤](microphone-audit-20261012.md)。本任务没有处理证书或密钥，也没有宣称语音输入已经实车恢复。
