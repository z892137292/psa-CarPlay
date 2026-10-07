# DiPlay 0.2.13: USB-only closed-TUN crash candidate

## Evidence boundary

Exact baseline: `shihabal3amri/DiPlay@6fb0fa4a09e77a84a437da5159147a6f6141ed61`.
No previous PSA patch is applied. No crash log from the affected device was
provided for this task. Therefore this change is a candidate for a demonstrable
USB exception path, **not confirmation of the user's actual crash root cause**.

## Static inspection

- USB attachment: `CarPlayHostActivity.isIphoneUsbAttachment/onNewIntent`,
  consent and permission result callbacks, normal controller startup.
- Apple USB permission requests, broadcasts and polling fallback;
  duplicate-grant suppression and configuration re-enumeration.
- `IphoneUsbHost`, `Iap2UsbSession`, `Iap2UsbMuxHost`, wired iAP2 control,
  NCM interface discovery/open/read and associated cleanup.
- `CarPlayController` wired startup, VPN binding/attachment, failure delivery,
  controller close, resource ownership and asynchronous teardown.
- `CarPlayVpnService.attach/releaseLocked/onTransportError` and its USB-only
  `Ipv6NcmBridge` worker threads.

Many USB setup failures already use error results or caught exceptions. There
are other unguarded callbacks/platform calls, but without a matching stack trace
they are not changed. No permission, re-enumeration, USBMUX, NCM framing, VPN
configuration or controller lifecycle policy is adjusted.

## Demonstrable defect and minimal change

Both `ncm-ipv6-in` and `ncm-ipv6-out` acquire `tun.fileDescriptor` and construct
their streams before entering their existing `try` block. If the TUN was already
closed, descriptor acquisition can throw `IllegalStateException` outside the
worker's error boundary. An uncaught background-thread exception can terminate
an Android application. USB teardown can close that descriptor while a newly
started worker is waiting to run.

Move stream creation into each existing `try` block. Nothing else is changed.
The existing `RuntimeException`/`IOException` catches now cover startup as well
as packet processing. When the bridge is still running the error goes to its
existing callback and the service's existing full-stack `Log.e`; after stop it
is ignored as before. No extra logger or global crash handler is introduced.

Actions runs the same closed-descriptor test against the untouched baseline
(expecting the exception to escape) and the candidate (expecting normal existing
error callback delivery). Tests cover both directions, running/stopped state,
Android 9/API 28 and API 33. Real closed `ParcelFileDescriptor.createPipe()`
descriptors are used; only the unused USB bridge is mocked.

## Exact changed-file inventory

Reconstructed Android project:

| File | Change |
| --- | --- |
| `shared/src/main/java/com/shilapi/xcertplay/network/Ipv6NcmBridge.kt` | Only two worker stream initializations moved into existing try blocks; two explanatory comments. |
| `common/src/test/java/com/shilapi/xcertplay/UsbNcmClosedTunTest.kt` | New closed-descriptor regression tests. |

Target repository delivery files:

- `patches/diplay-0.2.13-usb-only.patch`: exact source/test diff against fixed baseline.
- `scripts/verify_diplay_usb013_scope.py`: checks every baseline file byte-for-byte;
  accepts only the exact worker-initialization relocation and one added test.
- `.github/workflows/build-diplay-usb013.yml`: independent reconstruction,
  baseline reproduction, USB regression tests, debug APK build and artifacts.
- `USB-0.2.13-INVESTIGATION.md`: this evidence and log-capture record.

The workflow never applies `psa-main-*` patches. All other baseline source,
manifests, resources and Gradle build files must remain byte-identical. This
includes UI, video/audio, resolution, codecs, Bluetooth, hotspot, LAN, Bonjour
and wireless timing. Android `minSdk=28` and original source debug package
`com.shihab.diplay.hudtest` remain unchanged.

The APK uses upstream's debug build/signing configuration. It is a separate test
application, not an overwrite-signed official release. Its optional local
authentication assets are copied from the matching upstream 0.2.13 release in
temporary CI storage; no credentials are committed and no authentication code
is modified. Local Gradle download failed with `Network is unreachable`; CI
provides the existing upstream JDK 25/SDK/NDK toolchain.

## Required device evidence

Capture the ORIGINAL app first, beginning before attaching the iPhone and
continuing until at least 10-15 seconds after the crash. Do not filter by app
PID: a restart changes it, and native/system USB messages would be lost.

```sh
adb logcat -b all -v threadtime > DiPlay-0.2.13-USB-crash-logcat.txt
```

After reproducing, stop capture with Ctrl+C, then collect:

```sh
adb shell dumpsys usb > DiPlay-USB-state.txt
adb shell dumpsys package com.shihab.diplay > DiPlay-package-state.txt
```

For the debug candidate use `com.shihab.diplay.hudtest` in the package command.
Provide the complete `FATAL EXCEPTION` block, process/package, thread name,
exception, `Caused by` and stack trace, plus 30 seconds of context before it.
Look for `ncm-ipv6-in`/`ncm-ipv6-out`, `ParcelFileDescriptor.getFileDescriptor`,
`IllegalStateException: Already closed`, USB permission/reenumeration, USBMUX,
NCM/VPN and controller teardown messages. A matching trace would connect this
verified defect to the observed device crash; a different trace requires a
different narrowly scoped fix.

If there is no Java fatal exception, preserve `Fatal signal`, `DEBUG`,
`tombstoned`, `libusb`, `UsbHostManager` and `ActivityManager` messages. Collect
`adb bugreport DiPlay-USB-bugreport.zip` if a native crash or ANR is reported.

Test original and candidate separately with the same phone/cable, including
cold USB attach, grant/deny consent, re-enumeration, rapid unplug/replug and
disconnect during startup. Do not report the user's flash-crash as solved until
device evidence or repeatable on-device validation supports it.
