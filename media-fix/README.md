# AndroidPlay 1.2.0 母包媒体控制定点修复

这是指定母包的局部 Smali 补丁。测试 APK 私下交付，不进入 Git、Release 或 Actions。
状态：补丁、构建、静态检查及主机模拟测试完成；没有安装到 Android/PSA 车机，没有实车验收。

## 唯一输入

- 包名 `com.androidplay.app`，versionName `1.2.0`，versionCode `45`。
- 母包 SHA-256：`6e5f6c0ab10d16c2abaef6d00eda0e7c0a76d78c7eef55c942e8a0338ce83d5e`。
- 只修改 `classes3.dex`。完整调用链、安装限制见 `media-fix-report.md`、`rollback.md`。
- `media-fix.patch` 是针对指定母包通过下述 Apktool Smali 引擎解出的目录、以 `-p1` 应用的完整补丁。
- `src/` 是新增辅助类的可读 Java 源码；`scripts/adapt_smali.py` 记录原有三个类的精确改写过程。

## 工具

本次使用隔离目录内的 Temurin JDK 17、Apktool 2.12.1、Android Build Tools 35.0.0、Android API 28 和 JADX 1.5.3。
没有更改系统 Java 配置。系统包管理器不可用，因此使用便携工具。

| 工具包 | 下载地址 | SHA-256 |
| --- | --- | --- |
| Apktool 2.12.1 | https://github.com/iBotPeaches/Apktool/releases/download/v2.12.1/apktool_2.12.1.jar | `66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa` |
| Build Tools 35 | https://dl.google.com/android/repository/build-tools_r35_linux.zip | `bd3a4966912eb8b30ed0d00b0cda6b6543b949d5ffe00bea54c04c81e1561d88` |
| API 28 platform | https://dl.google.com/android/repository/platform-28_r06.zip | `8452dbbf9668a428abb243c4f02a943b7aa83af3cca627629a15c4c09f28e7bd` |
| JADX 1.5.3 | https://github.com/skylot/jadx/releases/download/v1.5.3/jadx-1.5.3.zip | `8280f3799c0273fe797a2bcd90258c943e451fd195f13d05400de5e6451d15ec` |

## 从完整 Smali 补丁复现

以下路径均替换为本机绝对路径。先备份母包；使用自己已有或另行创建的独立测试 PKCS12 密钥。
`--password-file` 是权限为 0600 的单行口令文件，测试密钥的私钥口令应与库口令一致。
不得使用、索取或伪造原应用签名。脚本不安装 APK，不清除数据，也不上传任何文件。

```sh
python3 scripts/build_test_apk.py \
  --mother /private/original/AndroidPlay-1.2.0.apk \
  --apktool /tools/apktool_2.12.1.jar \
  --build-tools /tools/android-15 \
  --jdk /tools/jdk-17 \
  --work /private/new-empty-build-directory \
  --keystore /private/test.p12 \
  --password-file /private/password.txt \
  --output /private/output/AndroidPlay-1.2.0-media-fix-test.apk
```

脚本先核对母包与 Apktool 哈希，仅从母包解出 `classes3.dex`，以零模糊匹配应用补丁并重新汇编。
其他 ZIP 条目从母包直接读入内存并写入新 APK，认证文件不导出为独立文件。
随后执行 16 KiB 原生库对齐、独立测试签名、签名验证以及逐条目/全部 DEX 校验。
已存在的输出文件及构建目录会导致中止，不会覆盖母包。

相同工具、同一测试密钥和相同输入已独立复现两次，最终 APK 字节一致。
使用另一个测试密钥时，APK 的签名和最终 SHA-256 必然不同；不承诺跨密钥二进制一致。
本仓库不保存测试私钥；未来如需延续同一测试签名，应由密钥持有人安全保管。

## 辅助类源码与测试

Java 源码已用 API 28 的 `android.jar` 编译，再经 D8（min-api 28）转换、Smali 反汇编后纳入完整补丁。
既有 Kotlin 类没有重新编译；它们的改动仅来自精确 Smali 注入。

```sh
python3 tests/run_tests.py /tools/jdk-17/bin/javac /tools/jdk-17/bin/java
python3 scripts/verify_apk.py /private/original/AndroidPlay-1.2.0.apk /private/output/AndroidPlay-1.2.0-media-fix-test.apk
```

`tests/run_tests.py` 执行实际 `PsaMediaControl.java`，用可控的 Android API 替身模拟焦点与回调。
这不是 Robolectric、Android instrumentation、ART 或实车测试。静态差异审计见 `evidence/method-diff.json`。
