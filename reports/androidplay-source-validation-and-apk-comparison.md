# PSA source validation and original APK comparison — 2026-10-09
Continued branch psa/androidplay-1.2.0-ipv4 from c895763ba07f9b762d7214e32727e57f6c0c6f72; no source baseline reset or protocol/UI changes.

## Environment
Complete Android tasks run in this project's GitHub Actions environment: Temurin JDK 25, Android SDK platform android-37.0, build-tools 36.0.0, NDK 29.0.14206865, project Gradle Wrapper. Runtime compatibility remains minSdk 28, not the SDK used to compile.
The interactive workspace has JDK 17 and downloaded Gradle but downloading the required JDK 25 is blocked by network access. No local complete SDK/NDK installation is claimed. The user is not required to have any old build environment.

## Independent checks
Workflow commit efa96ee4923ea46721e0e33086fa250cd1ac03ea moved unit tests and lint BEFORE authentication provisioning.
Run https://github.com/z892137292/psa-CarPlay/actions/runs/37873148606:
- Reviewed PSA patches applied and Gradle task configuration: PASS.
- :shared:testDebugUnitTest and :common:testDebugUnitTest: PASS.
- :mobile:lintDebug including API-28 compatibility: PASS (does not mean warning-free).
- Authentication provisioning gate: BLOCKED.
- Authenticated standalone APK compilation and verification: SKIPPED.
Report artifact 11591650383 contains only test and lint reports.
Subsequent workflow commit ac73a1a9c69ec71a19a4fb8eb4610208dc290d07 adds independent :mobile:assembleDebug with sourceOnly=true solely as code compilation verification. This APK is not uploaded or delivered as a CarPlay test build. Run https://github.com/z892137292/psa-CarPlay/actions/runs/37873166975 completed:
- Gradle configuration: PASS.
- All shared/common unit tests: PASS.
- Android lint: PASS.
- Independent source-only :mobile:assembleDebug compilation: PASS.
- Authorized authentication gate: BLOCKED, overall workflow correctly failed.
- Authenticated standalone APK: SKIPPED; no connection-capable APK delivered.
sourceOnly=true applies only to credential-independent checks. The standalone task always runs without sourceOnly and still rejects missing credentials.

## Original user APK comparison
AndroidPlay-1.2.0(1).apk, 15,378,441 bytes.
APK SHA-256: 6e5f6c0ab10d16c2abaef6d00eda0e7c0a76d78c7eef55c942e8a0338ce83d5e.
Zip metadata only:
- assets/offline-mfi/identity.pk8: 67 bytes, compressed 67 bytes.
- assets/offline-mfi/certificate.p7b: 607 bytes, compressed 459 bytes.
- Both entries use ZIP method 8 and are nonempty.
- Native libraries: arm64-v8a, armeabi-v7a, x86_64.
Neither credential entry was exported. This inspection proves presence, not certificate/private-key validity, signing compatibility or permission to reuse.

## Authentication provenance and permission
AndroidPlay docs/ANDROIDPLAY_AUTH_SOURCE.md records use of DiPlay 0.2.6's experimental identity. Current AndroidPlay notices explicitly say redistribution authorization remains unconfirmed.
DiPlay v0.2.6 docs/THIRD_PARTY_NOTICES.md describes an identity recovered from Carlinkit firmware and explicitly says the data are not relicensed as project source, with general distribution suitability unresolved.
This confirms reported provenance, not authorization. There is no affirmative private-test permission evidence in the inspected notices, nor public-redistribution permission. Private testing and public publication are separate decisions. No third-party credentials were extracted or provisioned.
Source references:
https://github.com/Roylyl/AndroidPlay/blob/793e488334a4e0c23459b659c271b7715ae9a9e7/docs/ANDROIDPLAY_AUTH_SOURCE.md
https://github.com/Roylyl/AndroidPlay/blob/793e488334a4e0c23459b659c271b7715ae9a9e7/docs/THIRD_PARTY_NOTICES.md
https://github.com/shihabal3amri/DiPlay/blob/v0.2.6/docs/THIRD_PARTY_NOTICES.md

## Preserved behavior
Static review confirms API28/ap0 actual IPv4 preference, scoped IPv6 fallback and unchanged selection elsewhere. Existing policy tests cover different actual IPv4, enumeration order, absent IPv4, invalid addresses, and other interface/SDK behavior.
UI retains default-hidden password toggle, nonplaintext hotspot summary with separately recorded source, and home disconnect calling existing resetWifi/CarPlayBackgroundSession.stop. No hotspot disabling is added. Existing hotspot checks/settings-return flow is retained.
Static/code tests do not prove actual PSA UI behavior.

## Acceptance status
No newly authenticated APK, no new connection-package SHA-256/signature fingerprint, and no newly observed phone connection.
PSA display, persistent black screen, Launcher return, audio/touch, 3 reconnection rounds, 15-minute stability and photo/video evidence: NOT TESTED / NOT PASSED.
Only authentication-enabled build and physical device acceptance remain dependent on authorized credentials and the actual vehicle.
Rollback: revert only this turn's workflow changes; all earlier PSA source patches remain intact.
