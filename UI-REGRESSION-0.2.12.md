# Restore PSA 0.2.12 host initialization

Baseline: PSA 0.2.11 `9d42ef33427ef402d1f52aae35bd0fd7922e2ccf`.
Candidate: PSA 0.2.12 `8e0b1ae41c9425b52c4e166658d76b570be9dcc8`.
Both complete patches are applied to DiPlay `3e43e25c55921bdf5149f5f92851acf202ed353a`.

## Cause and correction

0.2.12 replaced the host's entire initialization tail with an explicit-connect
restart. This omitted `setContentView(buildContentView())`, session log setup,
persisted settings, startup permissions, and background session adoption.
The restart also returns before a fresh host has an owner and display size.
Consequently a new host can show an empty window with no startup diagnostics.

Restore `onCreate` verbatim from 0.2.11. Remove the unused explicit-connect
intent flag from `DiPlayActivity.openProjection`; retain manual hotspot
confirmation. Returning to an existing host continues to reuse its session.

No new view, overlay, animation, resource, button or layout is introduced.
The preparation layout, stage strings and stream visibility callback retain
the 0.2.11 behavior. This fix does not introduce a new first-frame display
policy: the missing initialization is the demonstrated regression.

All other 0.2.12 production source files are byte-identical, including USB,
system hotspot, LAN selection, network timing, terminal events, reconnect,
controller close gating and asynchronous teardown. Wi-Fi Direct stays removed.

## Validation

- Reconstructed both pinned versions using the existing Actions process.
- Original 0.2.12 fails the initialization guard; repaired source passes.
- Complete repaired patch applies cleanly to the pinned upstream baseline.
- Only the two Activity files and the new preparation test differ from 0.2.12.
- Existing protected protocol/media source verification passes (86 files).
- Added Robolectric preparation-panel tests to the existing Android test command.
- Added the UI source guard before the existing Actions build.
- Local Gradle execution is blocked downloading Gradle 9.5.0 with
  `java.net.SocketException: Network is unreachable`. Local JDK is 17 and no
  Android SDK is configured; Actions retains JDK 25 and its existing SDK setup.

## Device regression checklist (requires real devices)

For USB, system hotspot and LAN: cold launch, tap Connect Phone, confirm the
original preparation/connection screen and working Back button, then connect
an iPhone and verify video/audio/touch. Test failure, iPhone disconnect,
Wi-Fi loss and reconnect. Confirm prompt return home on terminal loss and no
conflicting new controller while the old one closes. Returning from home to
an active projection must reuse the session without restarting it.

Automated tests cannot establish real-device behavior or network performance.
