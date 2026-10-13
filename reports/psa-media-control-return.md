# PSA 方向盘媒体控制返回修复审计

## 稳定 APK 对照

- 用户母包：`CarPlay-1.2.0(1).apk`
- SHA-256：`2b43c7b412271b137d3eeaddf9f5a97e2bcb94f3df525ea01b88585d0b507a30`
- 包名：`com.androidplay.app`
- 版本：`1.2.0` / Build 45
- minSdk：28；targetSdk：35
- 签名证书 SHA-256：`9aee4f702cac2e51ac7473604ac885ed924b2fda6f9b494a7eec2eb0252143d6`

仅对 DEX、Manifest 和公开签名信息进行了对照；没有提取认证资源。母包包含
`AndroidPlayMediaSession`，但没有本补丁新增的 `MediaKeyGate` 或
`AndroidPlayMediaButtonReceiver`。母包还包含仓库基线之外的修改，因此不能证明由当前公开
源码逐字节构建，也不能把源码构建产物冒充该稳定母包的等价版本。

## 已确认故障层级

原实现创建了 MediaSession 并处理播放、暂停、上一首、下一首，但存在三个缺口：

1. 没有为会话声明媒体按键与传输控制能力，也没有显式媒体按键接收器；
2. 失去音频焦点后没有主动让出 MediaSession；
3. 返回 `CarPlayHostActivity` 前台时没有一次性恢复焦点与会话。

DrivePlay 的 `dumpsys media_session` 只能证明系统当时选中了它的系统 UID 会话，不能证明其
OEM/MCU 完整链路适用于普通 APK。本补丁没有复制闭源实现，也没有猜测厂家广播。

## 最小修复

- 在 CarPlay 页面返回前台时，仅尝试一次 `AUDIOFOCUS_GAIN`；不会定时循环抢焦点；
- 收到永久焦点丢失时停用本应用 MediaSession，允许原车播放器接管；
- 后续元数据刷新不会重新抢回焦点；
- 使用 Android 公共媒体按键 API，过滤 ACTION_UP 和长按重复事件；
- 对同一物理按键被 Receiver/MediaSession 两路投递的情况去重；
- 继续复用原 `controller.sendMedia(1/2/4/5)`，不修改 CarPlay 协议；
- 日志标签 `PSA-MEDIA` 区分焦点、接收器、按键、回调和转发调用。普通 APK 无权直接读取
  全局媒体按键目标，因此实车需结合 `dumpsys media_session` 判断。

## 本地门禁（2026-10-13）

- JDK 25、Android Platform 37、Build Tools 36、NDK 29；
- shared 单元测试：205/205 通过；
- common 单元测试：62/62 通过；
- 新增 3 项按键去重测试和 2 项焦点/10 轮切换测试；
- `:mobile:lintDebug`：0 error，5 个既有 warning；
- `:mobile:assembleDebug`：通过；
- 源码验证 APK：包名正确、minSdk 28、v2 调试签名有效。

源码验证 APK 不含离线认证资源，明确不能用于 CarPlay 连接测试。当前仓库和 CI 没有可用的
私有认证输入，也没有保存母包后续修改的完整源码，因此尚不能生成与稳定母包等价的连接测试
APK。这是 APK 交付阻碍，不影响代码、单元测试和 CI 的完成。

## 待 PSA 实车验证

执行十轮：CarPlay → 原车音乐 → 停止原车音乐 → 返回 CarPlay。每轮分别按上一首、下一首、
暂停，确认只有当前播放器响应。同步保存：

```sh
su -c 'dumpsys media_session > /sdcard/Download/media-return-session.txt'
su -c 'dumpsys audio > /sdcard/Download/media-return-audio.txt'
su -c 'logcat -d -v threadtime -s PSA-MEDIA:* > /sdcard/Download/media-return-log.txt'
```

回滚时保留稳定母包与应用数据；由于调试签名与稳定签名不同，不能覆盖安装。未备份数据前不要
卸载稳定版。
