# PR #13 PSA Android 9 首帧发布门槛（测试候选）

## 真实环境与证据
目标为 PSA Android 9/API 28、spm8666p1_64、1920×720 横屏，目标密度 160dpi（需 adb 实测）。包名 com.psa.carplay.dev。USB 和外接 AP/LAN 曾经成功显示画面是用户提供的实机事实；本轮不能远程复现。
已取得真实 PSA_Launcher_final_1.1.apk，SHA256 4b82c1cd67ad90d756547914a66f6267f336c4578c68cd814779ef15e7f02c29。Manifest 与 DEX 静态分析见 PSA_LAUNCHER_COMPATIBILITY.md。它是桌面样本，不是 ROM；权限、接口能力不能据此确认。不修改 Launcher、HOME 默认应用或 ROM。

## 风险与最小修复
- CarPlayHostActivity.kt buildContentView：原有不透明准备面板、Kable 正在准备、进度与返回按钮保留，原视频渲染流程保留。
- updateDebugOverlays：只有 mainFirstFrameReady 且主视频流 active 才隐藏准备面板。Controller 启动、SETUP、收到数据或解码器创建均不能代替真正首帧。
- textureListener/onFirstFrameRendered：当前 Texture 更新证据和会话 generation 校验保留；增加主流 active 检查，忽略旧 Surface 的尺寸回调。
- armFirstFrameWait/onFirstFrameTimeout：Controller 启动后前台等待首帧最多 90 秒；未显示首帧则记录 FIRST_FRAME_TIMEOUT，回 PSA 首页，后台安全清理；人工重试，不缩短 USB/iAP2/MFi 协议超时。
- onPause/onResume/onDestroy：暂停时取消 UI 首帧计时，恢复时重新等待；不因暂停释放 Controller。已显示首帧不再计时，旧 generation 计时回调无效；同一前台会话重建 Surface 不延长已有截止时间。
- DiPlayActivity consumeConnectionFailure/refreshStatus：超时结果在刷新后仍可见，用户能重新选择连接方式；等待旧控制器退出时仍禁止新控制器。
- onNewIntent：重复有线 USB 接入复用已有 Controller，清理期间不重复切换；核心 USBMUX/iAP2/NCM/VPN/MFi 不修改。

## UI 与 Android 9
首页仅三栏：状态/连接按钮，USB/LAN/系统热点选择，真实已配对手机列表。设置和诊断在设置区域。准备面板与投屏 UI 分开。去掉首页二次全局缩放；160dpi 验证完整显示，其他密度验证正常 dp 控件可滚动到达，不能等同车机实际 DPI 验证。
检查发现 PR #13 原构建未接入 PR #11 的音频补丁，会重新带入已确认的 ROM getter 风险。PR #11 音频修复和 PR #12 ROM 测试现已进入本 PR 的源码重建流程。AudioTrack 属性由创建代码保存、fallback 保留实际属性；禁止危险 getAudioAttributes 调用，并模拟 NoSuchMethodError/音轨/解码器失败。所有新增生产 API 为 API28 可用 Handler/Runnable/Intent/Activity 生命周期调用。
没有恢复 P2P、自动 SoftAP 或改变已经工作的协议栈。无互联网 LAN 和 wlan0/ap0 选择测试来自 ROM 兼容套件。

## 自动化与限制
静态：正式树检查、保护协议源码字节检查、ROM 危险 API 检查、5 个检查器变异测试、UI/首帧检查。
JVM/Robolectric：原完整 shared/common/home 套件，加无首帧 90 秒恢复、握手不能隐藏准备面板、旧计时无效、首帧取消计时、真实 onPause/onResume 保留控制器并重新计时、USB/LAN 点击路由、重复 USB 复用、旧 Surface 回调、首页错误持久显示。模拟不能替代实机。
本地 Gradle 因下载网络不可达未运行；GitHub Actions 执行完整 Gradle 单测、lint、APK/Standalone/示例构建。具体结果在构建完成后补充。

## 必须待实机验证
打开首页；点击连接保留准备面板；USB/LAN 原路径出画面；首帧前无黑屏；无视频超时能重试；连接中返回；断线回主页；连续连接/断开/重进；PSA Launcher 前后台/HOME 切换；1920×720 实际密度/字体/触控；音视频连续播放；无崩溃或整机重启。未完成前仅标记测试候选。

## 回滚
不修改 cleanup/psa-formal 或 main。CI 保存在 Git bundle 内的本地标签 rollback/psa-pr13-before-first-frame-review-20261008 指向本次修改前 91e4b3922bc14b2c6d8863cc220d71934650447b（源码回滚点，不声称其 CI 或实机成功）。GitHub workflow token 缺少 workflows 权限，远端标签创建被拒绝；完整带标签备份在 Artifact，不冒充远端已创建。
车机安装前先备份当前已成功 APK（adb shell pm path com.psa.carplay.dev，再 adb pull 返回的 base.apk）；记录 SHA256/签名与版本。若测试破坏 USB/LAN、准备界面、恢复或导致重启，立即停止并恢复该实机已成功 APK。不要将任何 CI APK 冒充原实机成功版本。


## 最终 GitHub Actions 结果

已验证代码 commit：`e8ae951c38dc1a6b4ef9c8f5a14c7f6eb43ea02b`。
[Actions 37746047021](https://github.com/z892137292/psa-CarPlay/actions/runs/37746047021)，job 113207934036，success；Gradle BUILD SUCCESSFUL in 4m 12s。

| 项目 | 实际结果 |
|---|---|
| 静态守卫 | 正式树、保留协议 SHA256、ROM getter、原准备界面 SHA256 均通过；5 项变异回归通过 |
| JVM/模拟套件 | shared/common/home 的 testDebugUnitTest 全部任务成功，完整 XML 在 Artifact；包含缺失 ROM 方法、fallback、首帧/Surface/超时、真实暂停恢复、USB/LAN 点击路由、重复 USB、已配对设备选择和 HOME 返回 |
| lint | mobile/home/maphost 的 lintDebug 成功；警告与 XML 在 Artifact，不宣称零警告 |
| 构建 | mobile debug/standaloneDebug、home debug、maphost debug 成功 |
| APK 检查 | CI aapt 确认 com.psa.carplay.dev、minSdk 28；未声明 Wi-Fi Direct 功能，认证资源存在；apksigner verify 成功，具体证书见 APK-SIGNATURE.txt |
| 当前失败项 | 最新代码的上述 CI 任务无失败；不是实机通过 |
| 未执行 | adb/instrumentation、真实 Launcher 运行、车机实际 H.264/音频/USB/LAN/热点并发、连续重连及无黑屏/无重启验收 |
| 本地限制 | Gradle 下载网络不可达；最终工作区离线，未能下载最新 ZIP 另附本地 APK、重新解析最终 XML/DEX/证书。不把这部分未执行写成通过 |

下载：[Artifact 11535898325](https://github.com/z892137292/psa-CarPlay/actions/runs/37746047021/artifacts/11535898325)。
ZIP 内 `out/PSA-CarPlay-0.2.15-pr13-test1.apk` 为本轮测试 APK，另含测试 XML、lint、APK-INFO.txt、APK-SIGNATURE.txt、SHA256SUMS.txt、Gradle 完整日志和带标签备份。APK 为 Debug 测试候选，未做生产签名或实机认证。

构建历史如实保留：
- 37744371834：回滚标签远端推送被 workflows 权限限制拒绝，未执行 Gradle。
- 37744645902：shared 384、common 180、home 4；common 的 320dpi 滚动可见性检查 1 项失败，其他无失败/跳过。已改用 Android requestRectangleOnScreen，保留完整控件可见断言。
- 37745475630：Maven 429 限流导致依赖解析失败，未完成测试；只对 429 做有界重试，测试/编译失败不重试。
- 37745828139：补充同一会话 Surface 截止时间回归后被新提交的 concurrency 策略取消，不能写成通过。
- 37746047021：最新源代码完整通过，测试候选交付。

## 对应代码与差异

- `CarPlayHostActivity.kt::buildContentView`：原准备界面逐字节保留，SHA256 `6a2eaf8257e165f5c3fbd56374ba893b4db1871b60ffa5b136f66f12d8cc06f0`。
- `textureListener.onSurfaceTextureUpdated / onFirstFrameRendered / updateDebugOverlays`：当前 Texture、当前 generation、主流 active 和 FIRST_FRAME 联合门槛。
- `armFirstFrameWait / onFirstFrameTimeout / onPause / onResume`：前台 90 秒截止、暂停恢复、Surface 重建不延期。
- `returnHomeAfterConfirmedLoss / shutdown`：回 PSA 首页与异步旧会话清理。
- `onNewIntent`：清理中不重复切换；有线重复接入复用已有 Controller。
- `DiPlayActivity.kt::compactHome / connect / consumeConnectionFailure / refreshStatus`：三栏真实设备首页、连接路由、失败持久提示。
- `patches/psa-first-frame-release-gate.patch` 为本轮实际代码、资源与测试差异；首页/USB 插入过滤器由 `scripts/apply_safe_usb_ui_tune.py` 保留；音频和 ROM 的独立补丁仍在 `patches/`。

## 可操作回滚

远端标签受 GitHub integration 权限限制，未创建；Artifact 内的 `out/PSA-PR13-before-first-frame.bundle` 已包含完整历史与本地标签，并在工作区离线前完成 git bundle verify。
取得 bundle 后：
```sh
git fetch PSA-PR13-before-first-frame.bundle refs/tags/rollback/psa-pr13-before-first-frame-review-20261008:refs/tags/rollback/psa-pr13-before-first-frame-review-20261008
git switch --detach rollback/psa-pr13-before-first-frame-review-20261008
```
该源码点为 91e4b3922bc14b2c6d8863cc220d71934650447b，不冒充实机成功 APK。车机回滚应恢复安装前备份的原成功 APK；目前未取得其版本/签名/SHA256，不能用新 CI 包替代。正式 cleanup/psa-formal 和 main 保持不变。

报告补提交仅更新文档，不再次构建；APK 和实际通过结果对应上述代码 commit。
