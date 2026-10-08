# PSA Launcher 静态兼容性分析

样本：用户提供的 `PSA_Launcher_final_1.1.apk`，27620469 字节，SHA256 `4b82c1cd67ad90d756547914a66f6267f336c4578c68cd814779ef15e7f02c29`。实际 package=`com.android.launcher`，versionCode=1190，versionName=`v202403121759`，minSdk=23、targetSdk=27、compileSdk=30。文件名中的 1.1 不等同于 Manifest 版本。没有以其他 APK 代替，没有修改样本。

方法：Androguard 解码二进制 Manifest、DEX 指令；完整解码 Manifest 与元数据提交于 `docs/evidence/`。静态证据不能证明 ROM 已授予声明权限或 Launcher 的实际系统安装身份。

| 检查 | 静态证据与结论 | 实机待验证 |
|---|---|---|
| HOME/入口 | `com.android.launcher2.Launcher` 有 MAIN+HOME+DEFAULT+LAUNCHER；额外 HOME action。WallpaperChooser 为独立壁纸入口 | 默认 HOME 是否为该包 |
| 任务栈 | Launcher launchMode=2（singleTask），excludeFromRecents=true；startActivity 路径 addFlags=268435456（NEW_TASK），也使用 LauncherApps.startMainActivity | PSA 启动/重入是否同一任务；不能仅靠 APK 推定 OEM 任务管理 |
| 横屏 | Manifest screenOrientation=0（landscape），configChanges=0x4F0 | 1920×720 实际窗口与导航栏占用 |
| 系统栏 | onCreate setSystemUiVisibility=1792（LAYOUT_STABLE/LAYOUT_HIDE_NAVIGATION/LAYOUT_FULLSCREEN 布局 flags）；setupViews=1024（LAYOUT_FULLSCREEN）。onCreate 还设置 FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS(0x80000000)，status/navigation bar color=0（透明）；这些不是隐藏系统栏的充分证据 | ROM 是否覆盖沉浸式或强制导航栏 |
| PSA 启动 | PSA DiPlayActivity 是 LAUNCHER、singleTop，Host 是 singleTask。标准桌面应用启动，无专属 ROM 权限前提 | 冷启、热启、Launcher 再次点击 |
| 首帧 | PSA native TextureView 当前 SurfaceTexture 的更新触发 FIRST_FRAME；SETUP/流激活单独不会隐藏等待面板；旧 generation 和旧 Texture 均被拒绝 | 真正 H.264 输出可见、旋转/暂停恢复 |
| 断开返回 | PSA 明确启动 DiPlayActivity + CLEAR_TOP + page=home，finish Host，不发送 HOME category；新增 API28 模拟测试 | 断开后停留 PSA 首页，用户主动“车机桌面”按钮才打开 HOME |
| 设置 | PSA Wi-Fi 使用 WIFI_SETTINGS 路径；删除旧 BYD 专属 HOME 跳转，热点 TETHER_SETTINGS ；ROM 不提供入口时给出提示，蓝牙使用系统/已配对设备列表。Launcher DEX 有普通 SETTINGS action | 车机 OEM Settings 是否 resolve、返回 PSA 是否恢复正确页面 |
| 字体/DPI/触摸 | Launcher 声明横屏不证明 1920×720 正确；PR #13 首页取消二次全局缩放；mdpi 测完整显示，hdpi/xhdpi 测正常 dp 控件通过滚动到达，物理窗口均为 1920×720 | wm density、font_scale、实际最小触控区域；截图测量不能由静态 APK 代替 |

Launcher 声明 WRITE_SECURE_SETTINGS、FORCE_STOP_PACKAGES、INTERACT_ACROSS_USERS 等权限，也有厂商服务调用路径；声明不证明被授予。PSA 不要求这些权限，不以安装特权组件或修改 Launcher 为前提。静态分析未执行 Launcher，不代表其系统栏、桌面杀后台策略或 Settings 页面在车机上验证成功。

PR #13 窗口覆盖与焦点：只修改 DiPlayActivity 首页；Host 原不透明准备面板原样保留。当前 Texture 更新且主流 active 才显示视频；旧 Surface 尺寸回调忽略。onPause 取消显示等待超时但保留 Controller，onResume 重新等待。Launcher 遮盖窗口、强制抢焦点、OEM 杀后台行为仍须在车机检查，不能通过桌面 DEX 作无风险结论。详见 PSA_FIRST_FRAME_RELEASE_GATE.md。

Manifest 声明 SYSTEM_ALERT_WINDOW，主 Activity 的 windowSoftInputMode=0x20（adjustResize）。应在车机测试外部窗口、键盘和权限对话框的尺寸/焦点影响；声明不能证明已授予悬浮窗权限或已存在遮挡 PSA 的窗口。未修改 Launcher。
