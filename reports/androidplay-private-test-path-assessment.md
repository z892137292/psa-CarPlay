# PSA personal-test path assessment — 2026-10-09
Scope: one user's own PSA Android9 vehicle, noncommercial, no public authenticated APK release, no private credentials committed.

## One-time assessment
Code licenses and accessory credential permissions are separate. The inspected upstream notices do not establish a positive permission to copy/repackage the firmware-origin credential, nor an explicit prohibition on this specific personal test. This is unresolved permission evidence, not a finding that personal testing is illegal, not a requirement for an Apple authorization document, and not a platform-wide technical prohibition.
The user's previous instruction conditions credential copying on appropriate usage rights. No new evidence satisfying that condition has appeared. Public download and noncommercial intent alone do not establish it. We will not repeatedly ask the user to contact the author or find an old build environment.
No message was sent to an author or rights holder. No identity file was exported from the supplied APK.

## Available engineering work is completed
Latest independent source workflow 37873166975 passed Gradle configuration, shared/common unit tests, Android lint and source-only compile. No unauthenticated APK is delivered for connection testing.
Only CI/report changes have been made since c895763ba07f9b762d7214e32727e57f6c0c6f72. PSA IPv4/UI/protocol/audio/video changes remain untouched.
Source-only compilation is evidence of build correctness only, not a connection-capable deliverable.

## Existing authentication paths inspected
AndroidPlayBootstrap.ensure first tries LocalMfiAuthenticationClient.load in the app's existing noBackupFilesDir/offline-mfi. Only if it fails does the bootstrap copy APK assets. Thus valid existing private data can technically be reused without bundling credentials in a replacement APK.
Normal Android update additionally requires compatible signing and preservation of application data. The old APK does not supply its signing private key. We have no matching signing environment or physical device/cache inspection, so this path is conditional and cannot be claimed operational.
Do not uninstall/clear data, bypass Android signature checks, or label a source-only APK as standalone connection-capable.
Remote and hardware MFi code exists in CarPlayController, but AndroidPlayBootstrap forces LOCAL and fails without local identity. Those backends are NOT an immediate configuration-only fallback in this AndroidPlay build. Making them selectable requires a separately scoped bootstrap/settings change, not a protocol rewrite, and an actually available authorized hardware/service backend. Such changes are outside current frozen-code scope and were not made.

## Practical alternatives and limits
1. Compatible signed in-place update preserving already provisioned application identity: needs matching signing environment and device cache verification, neither currently available.
2. A separately provisioned authorized local identity: existing standalone task and original loader can be used without code changes; no such input is present.
3. Authorized hardware/remote authenticator: existing lower-layer implementations could be retained; needs a real backend and an explicitly scoped startup/configuration change. Not currently available and not silently introduced.
These are conditional alternatives, not claims of a ready-to-use APK. There is no proven configuration-only path among currently available inputs that produces a verified connection-capable package without using the unresolved third-party identity.

## Acceptance
Authenticated standalone APK not generated. PSA physical display, black-screen behavior, Launcher return, audio/touch and sustained reconnect tests remain NOT TESTED / NOT PASSED.
No requirement is placed on the user to supply a compilation environment. Complete Android builds run in the configured repository CI environment.
