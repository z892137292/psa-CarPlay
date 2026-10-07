# Bluetooth bootstrap and dedicated SoftAP transport

Working protocol baseline: PSA 0.2.12, including the host initialization fix,
commit c638f50a49d3f0386b95726ebcca37fdb1bda20b. The supplied successful
2026-10-07 LAN log reports this version, AirPlay/type-130/tunnel/video/audio.
Rebuild against pinned DiPlay 3e43e25c55921bdf5149f5f92851acf202ed353a;
this is the existing complete-patch project, not a separate demonstration.

## Architecture

ConnectionMode is AUTO, WIRELESS_AP, USB or EXISTING_LAN. AutoTransportManager
chooses an attempt; an Apple USB attachment never proves USB CarPlay active.
AUTO attempts USB when a device exists and marks active only from the actual
AirPlay session callback. On failure or 30-second session timeout it closes
the old controller, waits for awaitClosed, then requests wireless prerequisites
and starts Wireless AP. A failed/slow teardown blocks any replacement.
There is no concurrent transport handover or default LAN/P2P selection.
App-open automatic connection defaults on; a previously explicit user opt-out remains respected. With no identifiable paired iPhone the controller waits without opening an AP or starting a CarPlay session. Initial Android permission/VPN/root prompts are still platform requirements.

CarPlayController retains its USB bring-up implementation and its single
AirPlay/media/touch implementation. Wireless identification and MFi run first
on RFCOMM. Only their success invokes authenticatedEndpoint, creates the
generation-scoped BoundPhoneSession, then creates an AP or observes a manually
selected existing LAN. The identification's WirelessCarPlay component name is
an accessory label; every 0x5703/StartSession network field uses the live network.

The bound object records bootstrap acceptance, Bluetooth identity, transport
identifier, expected interface/address and AirPlay deviceID/sessionUUID. The
existing protocol identifies the accessory to the phone; it does not provide
a previously unknown phone serial number. This distinction is explicit rather
than inventing an iPhone identification payload. TCP is provisional; compressed and scoped IPv6 representations compare by address bytes. Known AP
neighbor addresses constrain peers when available. SETUP assigns one session
owner; changed peer/device/session and conflicting tunnel transport identities
are rejected. A deviceID matching another paired Bluetooth device is also rejected. A Wi-Fi MAC is not assumed to equal a Bluetooth MAC. Rejected or
stale sessions cannot replace the owner or trigger its UI disconnect.

## State machine

IDLE -> WAITING_FOR_PHONE -> BT_DISCOVERED -> BT_CONNECTING -> BT_IDENTIFIED
-> PHONE_BOUND -> SOFTAP_STARTING -> SOFTAP_READY -> AIRPLAY_WAITING
-> WAITING_PHONE_WIFI -> AIRPLAY_CONNECTED -> IAP_TUNNEL_STARTING
-> IAP_TUNNEL_READY -> WIRELESS_ACTIVE.
Existing LAN skips the SoftAP states. USB uses USB_CONNECTING -> USB_ACTIVE.
Terminal events enter DISCONNECTING; failures enter FAILED. Reconnect retains
the existing immediate-home callback and confirmed controller exit gate.
Bluetooth handoff requires a bound AirPlay owner, active AirPlay session and
ready authenticated type-130 tunnel. RFCOMM EOF after this remains normal.

## Real hotspot backends and limits

SessionSoftApManager tries RootSoftApBackend, then AndroidApiSoftApBackend.
The working PSA baseline has local ADB support but no general su executor.
The added bounded su executor verifies uid 0, quotes arguments, invokes the
APK's RootSoftApMain through app_process and never logs credentials.
RootSoftApMain calls platform methods by name rather than hardcoded Binder
transaction numbers: 5 GHz WPA2 configuration, platform tethering startup (legacy Connectivity service on Android 9, TetheringManager on modern releases),
live tethered interfaces, SoftApCallback/iw and the existing read-only WEXT radio reader, and IP neighbors.
ACS chooses a regulatory-supported channel rather than imposing an unsupported
36/40/44/48 channel. Root startup waits for actual interface and IPv4; the
live SSID/password must match the current request. DHCP is reported as system
tethering evidence, with leases explicitly unverified. Neighbor IPs are not
claimed to prove Bluetooth identity. Client count uses legacy Handler or modern Executor callbacks; it is explicitly unknown when the ROM cannot supply it. Root metadata polling slows from two to ten seconds after proven projection; local interface/address and readable driver frequency checks still run at the existing fast monitor cadence.

The Android backend owns a LocalOnlyHotspot reservation, attempts configurable
5 GHz startup where the API is available, otherwise reads the real reservation.
A 2.4 GHz or unknown channel fails explicitly; no fake channel/address and no
Wi-Fi Direct fallback. Android 9 public LOHS cannot reliably select 5 GHz;
root/privileged OEM APIs and live radio availability must be checked on-device.
The existing JNI WEXT reader supplements iw, including root-side loading for restricted drivers. Some ROMs hide tethering methods or lack live radio readings. These report capability
failure rather than pretending automatic CarPlay is working.

AP credentials are created per generation. AirPlay and interface mDNS use
the returned AP IPv4 and scoped IPv6 list. AP mode requires port 7000;
Existing LAN retains its previous port fallback behavior. AP cleanup owns
only the created hotspot. An already active system AP is not reconfigured
by the root backend. Failed cleanup prevents a second backend/controller.

## Experimental Wi-Fi Direct

The PSA 0.2.12 patch already deleted P2P production sources. Original pinned
upstream sources are retained byte-for-byte under experimental/wifi-direct,
outside Android source sets. There is no production factory call, AUTO route,
ordinary setting or automatic startup for them. They are disabled reference
code, not a working developer-mode connection option in this build.

## Logs (illustrative, not captured device results)

```
CONNECTION_TIMELINE connectionAttemptId=<uuid> generationId=<n> event=BT_RFCOMM elapsedMs=<measured>
CONNECTION_TIMELINE ... event=PHONE_BOUND ...
WIRELESS_AP_DIAG generationId=<n> boundPhone=<name> bluetoothAddress=<address> iap2Identity=accessory-identification-accepted transportIdentifier=<observed>
WIRELESS_AP_DIAG ... softApInterface=<live> softApSsid=<live> softApSecurity=WPA_WPA2 softApChannel=<live> softApFrequency=<live> softApIpv4=<live> softApIpv6=<live> softApClients=<observed-or-unknown> iphoneClientIp=<neighbors>
WIRELESS_AP_DIAG ... airplayBindInterface=<live> airplayPort=7000 bonjourA=<live> bonjourAAAA=<live> firstTcpPeer=<observed> airplaySession=<SETUP-uuid> tunnelReady=true wirelessActive=true
WIRELESS_AP_DIAG ... failureStage=SOFTAP_START_FAILED state=SOFTAP_STARTING detail=<actual-api-or-root-error>
```

Timeline also emits BT_FOUND, IAP2_READY, MFI_READY, SOFTAP_START, SOFTAP_READY,
WIFI_CONFIG_SENT, PHONE_JOINED (accepted session ownership); AP_CLIENT_SEEN separately records neighbor evidence, START_SESSION, FIRST_TCP,
AIRPLAY_SETUP, TYPE130_CREATED, TUNNEL_READY, FIRST_FRAME, FIRST_AUDIO and
WIRELESS_ACTIVE. FIRST_AUDIO uses the existing first PCM diagnostic. The type-130 response port is also recorded in WIRELESS_AP_DIAG.

## Validation boundary

verify_softap_scope.py checks 96 protected protocol/media/USB/MFi files and the
entire wired controller bring-up block against the reconstructed working
baseline byte-for-byte. AndroidMediaSink adds only one first-PCM diagnostic notification;
the scope check removes that exact line before byte comparison. Added tests cover session ownership, transport identity,
generation replacement, AUTO/USB teardown gates, timeline and real AP policy.
Existing wired encoding, USBMUX, AirPlay/type-130/media, terminal health, LAN,
Bonjour, preparation visibility and controller close tests run in Actions.
Actions runs full shared/common/mobile lint on both reconstructed revisions. Unfiltered XML/HTML reports are retained; a source-based comparison rejects every new error while reporting existing unrelated errors, instead of silently suppressing them or rewriting unrelated modules. It also builds the standalone APK with
the existing explicit upstream runtime authentication input. No authentication
files are committed. Local Gradle cannot download its distribution and has
no Android SDK, so Actions is the executable build environment.

The 19 requested physical tests require an iPhone and car unit. They have not
been performed here. Installation, automatic Wi-Fi join, actual TCP 7000,
tunnel handoff, rendered video/audio/touch, Wi-Fi-off/phone disconnect,
reconnect, repeated USB unplug/replug and manual Existing LAN must be verified
on hardware. Unit tests and an APK build do not prove these outcomes. The
previous DiPlay 0.2.13 USB crash investigation has no confirmed fatal log and
is not claimed fixed by this architecture change.

## Host startup regression correction

The first SoftAP APK accidentally removed the original onCreate initialization while changing an attachment branch. That prevented the preparation view, settings, identity, diagnostics and permission flow from being created. The original lifecycle initialization is restored; the layout is unchanged. CarPlayHostStartupTest runs real onCreate/start/resume/visible on API 28 in USB and Wireless AP modes, checks the actual window panel and startup fields, and holds hardware authorization pending. Only authentication asset provisioning is bypassed. The build also statically rejects missing startup calls in the reconstructed patch. VersionCode 215 identifies this correction. Hardware acceptance remains required.
