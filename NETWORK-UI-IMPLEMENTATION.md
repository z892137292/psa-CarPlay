# PSA 0.2.16: 1920×720 and network identity

Design baseline: 1920×720 landscape at 160dpi. Layout uses dp/sp, 64dp header, 256dp navigation on wide screens, side-by-side home cards. Narrow or high-density screens retain a compact rail and scrolling content. 2250×1080 is no longer the acceptance baseline. Decoder canvas is unchanged.

Wi-Fi button: `common/.../NetworkSettingsLauncher.kt`: ACTION_WIFI_SETTINGS → ACTION_WIRELESS_SETTINGS → ACTION_SETTINGS. Hotspot has a separate button: TETHER_SETTINGS → WIFI_AP_SETTINGS → network/settings fallbacks. Explicit network metadata is retained in exported logs while credential/payload filtering remains in place. Each attempt records SETTINGS_INTENT requestedAction/resolvedPackage/resolvedActivity/success. Resolution can be redacted on newer Android; actual launch exceptions determine fallback. Emulator checks actual resumed WifiSettings, not just resolution. Vendor ROM hotspot deep-link must be checked on the vehicle.

SSID: `shared/.../network/NetworkIdentityResolver.kt`: actual Wi-Fi NetworkCapabilities and LinkProperties; API29+ WifiInfo transportInfo; legacy WifiManager only when exactly one physical STA interface is visible and legacy networkId is valid. Checks fine/coarse location by SDK, LocationManager.isLocationEnabled, and reports nearby Wi-Fi permission independently (nearby is not a replacement for fine location to read SSID). Existing Host permission requests retain Android9 location and Android13 nearby/fine location. Diagnostics never silently treat unreadable SSID as success. normalizeSsid rejects placeholders and removes outer quotes; ExistingWifiManager fails clearly if live identity cannot be read. No cached SSID alone qualifies.

STA/AP: ExistingWifiManager requires OS Wi-Fi capability, excludes VPN, reported tethering interfaces and P2P. AP reader uses system hotspot config, never STA WifiInfo; auto interface selection requires OS tethering evidence, or explicit interface hint with AP not reported disabled; unreadable AP state still requires the existing per-attempt manual confirmation before transport attaches. Interface name alone is not evidence. If ROM redacts evidence, refuse ambiguous assignment and ask for explicit configuration rather than inventing a role/IP/SSID. Roles are STA/AP/P2P/USB_NCM/TUN/UNKNOWN; non-Wi-Fi roles require explicit transport evidence, not a wlan name. Duplicate Network handles for the same live interface/address use existing LanNetworkSelection de-duplication.

Network readiness is not CarPlay success. `orchestration/ExistingLanSuccessEvidence.kt` accepts only current generation and requires ALL: PHONE_BOUND, NETWORK_VERIFIED, LISTENER_BOUND, START_SESSION, FIRST_TCP_EXTERNAL, AIRPLAY_SETUP, TYPE130_CREATED, IAP_TUNNEL_READY, FIRST_FRAME, WIRELESS_ACTIVE. Terminal ends the proof; old events cannot complete it. Logs are diagnostic only and do not rewrite protocol or change transport admission. Setup ownership accepted is paired with actual session activation and tunnel/frame events before success. Listener binds real address confirmed against live interface; no process-wide network routing change.

Example (illustrative fields, not a hardware result):
```
NETWORK_MODE_DIAG selectedMode=EXISTING_LAN resolvedMode=EXISTING_LAN staNetworkCount=2 staInterface=<live> staSsidRaw=<raw> staSsidNormalized=<normalized> staBssid=<live> staIpv4=<live> staIpv6=<live> staFrequency=<live> staRssi=<live> ssidPermission=true locationEnabled=true nearbyWifiPermission=true ssidStatus=SSID_CONFIRMED
NETWORK_MODE_SOURCE requestedMode=EXISTING_LAN resolvedMode=EXISTING_LAN interface=<live> ssid=<normalized>
EXISTING_LAN_NETWORK_VERIFIED role=STA iface=<live> ...
AIRPLAY_LISTENER_BOUND_TO_NETWORK generationId=<current> interface=<live> address=<live> port=7000
EXISTING_LAN_PROGRESS generationId=<current> stage=FIRST_TCP_EXTERNAL success=false
EXISTING_LAN_SUCCESS generationId=<current> stages=PHONE_BOUND,NETWORK_VERIFIED,LISTENER_BOUND,START_SESSION,FIRST_TCP_EXTERNAL,AIRPLAY_SETUP,TYPE130_CREATED,IAP_TUNNEL_READY,FIRST_FRAME,WIRELESS_ACTIVE success=true
```

Scope: CHANGED-SOURCE-NETWORK-UI.txt and patches/psa-0.2.15-to-0.2.16-network-ui.diff list changes against the shipped 0.2.15. No USB bring-up, USBMUX, NCM, iAP2, MFi, encryption, codec, audio or touch implementation changes. Bluetooth list and ManualHotspotManager retained. Wi-Fi Direct stays outside default flows. Existing FIRST_FRAME decoder + TextureView gate remains intact.

Physical iPhone and vehicle ROM unavailable in this environment. Previous Wi-Fi-attached/AirPlay-connected logs prove only those stages; no Existing LAN complete-success claim is made. Re-test actual LAN with the new generation-scoped logs, SSID and network evidence, TCP, setup, type130, tunnel, frame and active events. Tests and installed-emulator screenshots do not prove USB or wireless success on real hardware.

Launcher environment analysis and current Manual Hotspot evidence/limits: see LAUNCHER-BASELINE.md. Exact numbered screenshots are produced by installed-APK tests; vehicle/ARM64 Launcher tests remain unperformed.
