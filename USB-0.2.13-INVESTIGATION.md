# DiPlay 0.2.13 USB flash-crash investigation (cause unconfirmed)

## Scope and result

Exact baseline: `shihabal3amri/DiPlay@6fb0fa4a09e77a84a437da5159147a6f6141ed61`.
No previous PSA patch is applied. No device crash log was provided. Static
inspection does not establish the actual USB flash-crash cause. **There is no
runtime fix in this branch and no claim that the device crash is solved.**

## Inspected paths

| Area | Source and result |
| --- | --- |
| USB attachment and consent | `CarPlayHostActivity.isIphoneUsbAttachment/onNewIntent`, startup permission/VPN callbacks and controller startup inspected. No matching device exception supplied. |
| Permission and re-enumeration | `IphoneUsbHost` request/broadcast parsing, controller permission polling and duplicate-grant guard, Apple configuration transition inspected. Setup failures generally return failed results; unguarded callbacks need a matching fatal trace before alteration. |
| USBMUX | `Iap2UsbSession`, `Iap2UsbMuxHost`, framing/read queue and wired control inspected. Reader loop already catches USB/RuntimeException; no observed device/native stack proves a failure here. |
| NCM/VPN | NCM discovery/open/read, VPN binding/attachment and `Ipv6NcmBridge` workers inspected. Cannot identify a confirmed flash-crash from source alone. |
| Lifecycle | Controller close, USBMUX/VPN ownership, asynchronous resource release and existing callback generation checks inspected. No speculative lifecycle changes made. |

A provisional closed-TUN hypothesis was checked and withdrawn. Android 9
`ParcelFileDescriptor.getFileDescriptor()` returns the underlying descriptor;
it does not enforce the hypothesized closed-state IllegalStateException.
`getFd()` is a different method. Moving stream constructors into another catch
boundary without a reproduced device exception would not meet this task's
evidence requirement. The candidate patch/test was discarded, draft PR #7
closed without merging, and the final Android source is completely unchanged.

Existing `xcertplay-usb` stage/error logging plus Android's fatal/native crash
logging should first be captured. No global crash handler or runtime logging
wrapper is added. A follow-up can add a narrowly targeted checkpoint if the
captured exception context proves the existing diagnostics insufficient.

## Actual changed files and diff proof

Android project: **0 changed production, test, resource, manifest or build files**.
The scope verifier compares all 808 pinned upstream files byte-for-byte,
rejects added source files, and confirms the pinned HEAD. The artifact contains
an empty `USB-SOURCE-DIFF.patch` and `USB-SCOPE.txt` as machine-verifiable evidence.
UI, hotspots, LAN, Bluetooth, Bonjour, wireless timing, video/audio, codecs,
resolution, USBMUX, NCM/VPN and controller lifecycle therefore remain unchanged.

Only three delivery files are added to the target repository:

1. `.github/workflows/build-diplay-usb013.yml`: independent unchanged-source build
   and existing USB tests; never applies `psa-main-*` patches.
2. `scripts/verify_diplay_usb013_scope.py`: exact-source scope guard.
3. `USB-0.2.13-INVESTIGATION.md`: this report and log capture instructions.

The workflow uses upstream's JDK 25, SDK 37 and NDK toolchain and checks
`minSdk=28`. Local Gradle download failed with `Network is unreachable`, so
Android tests and APK build run on Actions. The APK is the original source's
debug variant, package `com.shihab.diplay.hudtest`, signed with a debug certificate.
It is a separate investigation app, not an overwrite-signed official release.
Existing local authentication assets are copied from the matching upstream
0.2.13 APK into temporary build storage; no credentials are committed and no
authentication implementation/settings are changed. Separate app storage means
the investigation app does not inherit the original app's settings or pairing.

## Required device logcat

Capture the ORIGINAL crashing app first. Start before USB attachment and retain
at least 30 seconds before the failure and 10-15 seconds afterward. Do not filter
by app PID: a restart changes it, and native/system USB messages would be lost.

```sh
adb logcat -b all -v threadtime > DiPlay-0.2.13-USB-crash-logcat.txt
```

Attach/unlock the iPhone, reproduce the flash-crash, wait 10-15 seconds, then
stop capture with Ctrl+C. Also collect:

```sh
adb shell dumpsys usb > DiPlay-USB-state.txt
adb shell dumpsys package com.shihab.diplay > DiPlay-package-state.txt
```

For the debug investigation app the package is `com.shihab.diplay.hudtest`.
The necessary section is the complete `FATAL EXCEPTION` block including process,
package, thread name, exception type, all `Caused by` entries and the full stack,
with preceding USB permission/reenumeration, USBMUX, NCM/VPN and teardown messages.

If no Java fatal exception exists, retain `Fatal signal`, `DEBUG`, `tombstoned`,
`libusb`, `UsbHostManager`, `AndroidRuntime` and `ActivityManager`. For native
crash/ANR evidence collect `adb bugreport DiPlay-USB-bugreport.zip`.
Record Android version, exact installed app version/package, whether the crash
occurs at USB attachment, permission acceptance, re-enumeration or projection
startup, and whether the process dies or only the Activity closes.

Only after this evidence identifies the failing path should a minimal fix be
implemented and verified against the same phone/cable and Android 9 behavior.
