# PSA Launcher installation baseline

Sample: PSA_Launcher_final_1.1.apk (27,620,469 bytes), SHA-256 `4b82c1cd67ad90d756547914a66f6267f336c4578c68cd814779ef15e7f02c29`.
Static analysis used the APK's binary AndroidManifest.xml, resources qualifiers and DEX instructions. The Launcher was not modified. The sample binary is not redistributed in this source repository.

| Item | Actual sample evidence | PSA adaptation |
|---|---|---|
| Package / HOME | com.android.launcher / com.android.launcher2.Launcher; MAIN + HOME + DEFAULT + LAUNCHER | Use Android's selected HOME; do not force another launcher |
| SDK / version | min 23, target 27; versionCode 1190, versionName v202403121759 | PSA remains min 28; sample filename is not its manifest version |
| Orientation | Manifest landscape (0); rotation helpers can temporarily lock/unlock based on rotation configuration | Main target 1920×720 landscape; retain configuration handling and independent video canvas |
| Launch mode | singleTask (2), excludeFromRecents; configChanges 0x4f0 | PSA DiPlay singleTop / video Host singleTask; preserve foreground session |
| Window | Launcher.onCreate: DRAW_SYSTEM_BAR_BACKGROUNDS 0x80000000; systemUiVisibility 1792 (LAYOUT_STABLE/HIDE_NAVIGATION/FULLSCREEN layout flags); transparent navigation/status colors. setupViews also sets LAYOUT_FULLSCREEN (1024) | Layout flags alone do not prove bars are hidden; PSA applies its own fullscreen mode and live window dimensions |
| Back | Launcher.onBackPressed returns app drawer to workspace, closes folder/edit state; does not call finish for the normal HOME workspace | PSA page Back returns to PSA home; root Back delegates Android task return; in-session UI Return keeps session alive |
| App launching | startActivitySafely delegates Launcher.startActivity and catches failures; app shortcuts are Android Intent based | Keep PSA MAIN/LAUNCHER entry; no arbitrary launcher-package intent redirects |
| Settings | Launcher options include android.settings.SETTINGS; bundled GlobalUtils.goSystemSettings explicitly targets com.android.settings/com.android.settings.Settings. Bundled NetworkUtils.openWirelessSettings uses WIRELESS_SETTINGS, which does not mean WLAN | PSA Wi-Fi begins WIFI_SETTINGS; hotspot begins TETHER_SETTINGS then WIFI_AP_SETTINGS. Actual resolved package/activity is logged separately |
| Size | Resource variants include layout-land, layout-port, layout-sw600dp, layout-sw720dp and mdpi/hdpi/xhdpi assets; uses Resources dimensions. Manifest does not declare a fixed pixel window | 1920×720 acceptance, dp/sp runtime layout; never reuse negotiation resolution for UI |
| Runtime dependencies | Only arm64-v8a native libraries; requests vehicle android.car and privileged system permissions | The x86_64 AOSP emulator cannot prove the sample's vehicle runtime; no system permission assumed from Launcher |

## Exact limits of this analysis

This APK is a HOME application, not firmware. It cannot reveal the vehicle's actual Settings Intent resolver, Wi-Fi/SSID permissions, hotspot API, Android Car service availability or OEM navigation-bar behavior. Those need vehicle logcat/dumpsys and runtime checks. Static presence of a bundled helper is not proof that every visible Launcher button calls it.

Current build environment has no local Android SDK, adb or KVM. CI's installed-APK UI tests run Android 9 x86_64 at a native 1920×720 display. They do not run this ARM64 vehicle Launcher. Launcher HOME/back return and active iPhone session restore on the vehicle remain NOT PERFORMED, and are not presented as passed.

## Current application changes

The homepage and connection shell keep the opaque real UI above the live TextureView until current-generation decoder first-render AND the current texture update. AirPlay setup/active alone cannot uncover it. Texture destruction resets display readiness; terminal events restore UI before asynchronous teardown. The real Bluetooth/USB/AirPlay start path remains present.

Hotspot settings has its own homepage/loading button; Wi-Fi has a separate settings button. Settings attempts log `SETTINGS_INTENT requestedAction= resolvedPackage= resolvedActivity= success=`. For non-Activity callers, NEW_TASK is used. No sample-derived ROM package is hardcoded.

Manual system-hotspot is the existing default; RootSoftAP/LocalOnlyHotspot are not promoted and Wi-Fi Direct stays experimental. No automatic manual-to-LAN fallback is added. NETWORK_MODE_SOURCE records requested/resolved modes and fallbackMode=NONE. Configuration display is labelled configuredNetworkMode, not actual resolved transport.

The network proof tracker now also emits MANUAL_HOTSPOT_SUCCESS only after all LAN-style session milestones plus real hotspot parameter validation, actual Wi-Fi-configuration transmit and an admitted external IPv4 peer on the live AP interface/subnet. Peer observation is explicitly `source=external_tcp_on_verified_ap_subnet`, not a fabricated DHCP client list. Session ownership, setup, type130, authenticated tunnel, first frame and active are also required. Unavailable evidence means no success log. Existing LAN is independently proved; a hotspot result cannot emit LAN success.

Paired-phone data remains Android bondedDevices plus actual ACL/bond updates, ordered bound/connected/iPhone/other. Preferred phone is per connection; no synthetic phones. USB implementations and complete USB controller startup are checked unchanged.
