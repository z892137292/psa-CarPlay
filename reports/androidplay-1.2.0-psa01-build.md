# AndroidPlay PSA Build 46 编译结果

2026-10-09：GitHub Actions 构建完成，结论 success。

- 版本：1.2.0-psa01 / Build 46；包名 com.androidplay.app；minSdk28；targetSdk35。
- 构建提交：1480b1cb552c37d9a6f0fed1c360417fdf85232f。
- 固定 AndroidPlay 基线：793e488334a4e0c23459b659c271b7715ae9a9e7。
- shared 单元测试：205项，0失败，0跳过。
- common 单元测试：57项，0失败，0跳过。
- Android Lint：0 errors / 6 warnings。
- APK 编译：通过；debug签名，安装前需确认与原APK签名是否一致，不要自动卸载。
- APK SHA-256：94e074ec7af616e3181adc0dd7e665d06d3d38d2247f942389d2068c526719a4。

[编译记录及APK artifact](https://github.com/z892137292/psa-CarPlay/actions/runs/37869088743)

产物名：AndroidPlay-1.2.0-psa01-B46-SOURCE-ONLY-debug-NO-CARPLAY-AUTH.apk。

**这是无运行时认证的源码验证包，不能用于iPhone CarPlay实测。** 本次没有配置明确授权的MFi认证Secrets，APK内已检查不存在assets/offline-mfi认证文件。不能因为编译成功将其当作真实可连接的PSA测试版。

实测版本仍需合法的运行时认证配置和匹配的签名环境。真机出画面、音频、触摸、3轮重连、连续15分钟及屏幕照片/视频与日志均未验收，状态未通过。

原main与已有DiPlay成功基线未修改。仅新增独立AndroidPlay测试分支及其编译流水线。构建artifact保留14天，完整报告和补丁存于本测试分支。
