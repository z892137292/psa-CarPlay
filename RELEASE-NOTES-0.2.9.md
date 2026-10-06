# PSA CarPlay 0.2.9-dev — Direct 生命周期与安全诊断

基线：DiPlay v0.2.10 / `3e43e25c55921bdf5149f5f92851acf202ed353a`，完整还原 PSA 0.2.8 后修改。新补丁独立应用，不叠加旧补丁。保留原有认证资源临时注入机制。

## 本次修改

- Android 9 Direct 网络由进程唯一的网络管理器及独立前台服务保留，会话结束/界面重进不删除 Group。创建、复用、释放、健康检查串行执行。读取本次真实 SSID、凭据、接口/IP、可读取的实际频率；不缓存 Wi-Fi 密码。
- 复用需要本进程成功创建的证据、真实 GO 状态、在线接口及含凭据的完整现场指纹。Android 9 公共 API 无法证明跨进程的应用归属，因此进程重启后已有 Group 采取保守拒绝策略，不接管、不删除。用户需在系统界面确认并关闭旧网络后人工恢复。可能的 HiCar 占用仅报告，不停止原厂服务。
- `removeGroup()` 成功回调仅代表接受请求，还必须实际观察 Group 消失。超时、BUSY、Channel 异常及未知归属锁定失败；每次人工恢复最多一次创建请求，没有密集自动重试。
- 旧控制器关闭超时后禁止启动新控制器，后台会话在关闭期间保留排他门。`awaitClosed()` 同时要求各工作线程退出。
- Direct 会话故障保留 Group，暂停自动恢复并提供人工恢复按钮。普通热点最多重试三次；USB 不自动重试，授权路径保留。
- A 仅 Direct；B Direct + 蓝牙/iAP2/MFi（无 AirPlay）；C AirPlay 控制及数据隧道（不启动屏幕/音频/麦克风流）；D 完整 CarPlay。默认 A，USB 始终使用完整原有路径。设置→PSA Direct 分阶段诊断提供阶段选择、启动、停止会话、关闭网络及人工解除暂停。
- Direct 自动恢复安全开关默认关闭。以持久化运行标记及内核 boot_id 检测“Direct 运行后出现新启动”；这只是相关性证据，不能认定重启根因。检测到后暂停，人工解除。boot_id 不可读时保守暂停。
- Android 9 报告优先自动保存到 `Download/PSA/Reports`，申请系统存储权限；拒绝/写入失败时退回应用外部专属目录，再退回内部 Reports。显示真实路径和失败原因。Android 10+ 用 MediaStore，同样提供回退。
- Direct 日志独立写盘并 sync，限量轮转，不只保存在内存中；普通会话保留已有历史日志。允许严格格式的 SSID/接口/IP/频率诊断，禁止密码和协议凭据。Boot Reason 在可用时写入报告。

## 不变范围

没有移植 0.2.11 Direct 实现；旋转/分辨率、AirPlay 协议、MFi 本地认证、iAP2 协议、视频解码参数、音频路由和已有握手参数保持 0.2.8 基线。

## 验证与限制

Actions 执行网络生命周期模型、关闭门禁、报告存储/回退、USB 控制协议、权限迁移和既有旋转/Bonjour/地址选择回归测试，再构建独立 Android 9 开发 APK。测试报告随 Actions artifact 提供。模型测试不能证明 Android 驱动或 PSA 硬件稳定。

全部硬件用例均待 PSA 车机实测：A 连续开关五次、界面退出重进五次、真实 Channel/BUSY/removeGroup 超时、HiCar 共存、车机休眠唤醒、USB 回归、B/C 分阶段连接，最后才 D 完整音视频与触摸。首次遇到整机重启立即停止复测，保存系统日志/Boot Reason；不得把小米手机日志作为车机根因证据。

开发 APK 使用现有 CI debug 签名机制；不同 runner 的 debug key 可能不同。CI 输出签名证书摘要，不承诺覆盖安装兼容。若与已安装 0.2.8 证书不同，需备份配置后卸载旧开发版，或由维护者用既有私有签名环境重签。本仓库不提交/复制签名私钥。

## ADB 提取

公共目录：`adb pull /sdcard/Download/PSA/Reports`

外部专属：`adb pull /sdcard/Android/data/com.psa.carplay.dev/files/Reports`

内部报告：`adb shell run-as com.psa.carplay.dev ls files/Reports`，随后 `adb exec-out run-as com.psa.carplay.dev cat files/Reports/<报告名> > report.txt`

历史日志：`adb exec-out run-as com.psa.carplay.dev cat files/logs/direct.log > direct.log`；同时提取 `diplay.log` 与 `previous*.log`。系统重启必须另外抓 `adb logcat -b all`、系统 boot reason 与可读取的 pstore；APP 无权限时报告未知。
