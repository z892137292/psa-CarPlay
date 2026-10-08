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
PR #11 音频修复和 PR #12 ROM 测试进入本 PR 的源码重建流程。AudioTrack 属性由创建代码保存、fallback 保留实际属性；禁止危险 getAudioAttributes 调用，并模拟 NoSuchMethodError/音轨/解码器失败。所有新增生产 API 为 API28 可用 Handler/Runnable/Intent/Activity 生命周期调用。
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
