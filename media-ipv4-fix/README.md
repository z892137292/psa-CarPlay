# AndroidPlay 母包：媒体控制 + Android 9/ap0 IPv4 优先

这是同一指定母包上的合并补丁。保留 `media-fix` 版本的完整媒体控制修改，并合入既有母包补丁中的两个网络文件片段，不合入热点 UI 改动。

母包 SHA-256：`6e5f6c0ab10d16c2abaef6d00eda0e7c0a76d78c7eef55c942e8a0338ce83d5e`。

- `media-ipv4-fix.patch`：从原母包一步复现两项修改的完整补丁。
- `ipv4-only.patch`：从既有 `androidplay-apk-patch/psa-mother-apk.patch` 原样提取的网络修改。
- `scripts/build_test_apk.py`：哈希门禁、Smali 修改、构建、独立签名及检查。
- `scripts/verify_apk.py`：只允许 classes3.dex、classes8.dex 内容改变，其余条目必须逐字节一致。
- `src/` 和 `tests/`：媒体门控可读代码及主机模拟测试；不是 Android 或车机测试。
- `scripts/adapt_smali.py`：媒体修改的维护脚本；完整构建使用合并补丁，不需要另运行它。

## 工具与复现

使用 JDK 17、Apktool 2.12.1、Android Build Tools 35.0.0、Python 3 和 patch。
脚本固定核对 Apktool SHA-256 `66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa`。

官方工具地址：
- https://github.com/iBotPeaches/Apktool/releases/download/v2.12.1/apktool_2.12.1.jar
- https://dl.google.com/android/repository/build-tools_r35_linux.zip

Build Tools ZIP SHA-256：`bd3a4966912eb8b30ed0d00b0cda6b6543b949d5ffe00bea54c04c81e1561d88`。

```sh
python3 scripts/build_test_apk.py \
  --mother /private/original/AndroidPlay-1.2.0.apk \
  --apktool /tools/apktool.jar \
  --build-tools /tools/android-15 \
  --jdk /tools/jdk-17 \
  --work /private/new-build-directory \
  --keystore /private/test.p12 \
  --password-file /private/password.txt \
  --output /private/output/AndroidPlay-1.2.0-media-ipv4-fix-test.apk
python3 tests/run_tests.py /tools/jdk-17/bin/javac /tools/jdk-17/bin/java
```

使用自己的独立 PKCS12 测试密钥；口令文件权限 0600。别名默认 `psa-media-test`，私钥与库口令相同。不得冒用原签名。
脚本不会覆盖已有输出或构建目录，不安装 APK、不清除车机数据、不上传 APK/密钥。认证资产仅在 APK 间原样复制。
不同签名密钥会产生不同 APK 哈希。详细实测结果与安装限制见 `media-ipv4-fix-report.md` 和 `rollback-media-ipv4.md`。
