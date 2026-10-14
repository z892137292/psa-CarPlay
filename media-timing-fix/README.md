# 返回 CarPlay 媒体控制恢复时机修复

唯一输入是已修好媒体控制及 IPv4 的最新合并 APK，SHA-256：
`968c4c2bf8aa9187ae4cd619cb59c4eaf1e4792f0ba002d773cebdf38ca2c311`。
禁止将初始 AndroidPlay-1.2.0.apk 作为输入；构建脚本会拒绝。

工具：JDK 17、Python 3、patch、Apktool 2.12.1、Android Build Tools 35.0.0。
Apktool 固定 SHA-256 为 `66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa`。

```sh
python3 scripts/build_test_apk.py --mother /private/AndroidPlay-1.2.0-media-ipv4-fix-test.apk --apktool /tools/apktool.jar --build-tools /tools/android-15 --jdk /tools/jdk-17 --work /private/new-timing-build --keystore /private/test.p12 --password-file /private/password.txt --output /private/AndroidPlay-1.2.0-media-timing-fix-test.apk
python3 tests/run_tests.py /tools/jdk-17/bin/javac /tools/jdk-17/bin/java
```

保留参数名 --mother 以兼容原构建脚本，但其含义已经固定为最新合并基准。
使用独立测试密钥，默认别名 psa-media-test。密钥不随交付提供；换密钥后签名和 APK 哈希不同。
构建脚本拒绝覆盖输出和工作目录，只组装 classes3.dex；其他 ZIP 条目原样复制。补丁必须零模糊应用。
verify_methods.py 仅允许 PsaMediaControl 的 restoreOnce、refreshActive 两个方法改变。
Java 源文件用于可读审查及主机模拟测试；APK 实际应用 media-timing.patch 中的 Smali 修改。
主机模拟不等于 Android ART、车机或真实方向盘通道验证。
