# AndroidPlay PSA standalone authentication packaging repair
Date: 2026-10-09

## Outcome
BLOCKED: no new connection-capable APK was produced. Authentication packaging validation is NOT PASSED. Physical PSA CarPlay display acceptance is NOT TESTED / NOT PASSED.

## Preserved baseline
AndroidPlay original 1.2.0 Build 45: 793e488334a4e0c23459b659c271b7715ae9a9e7.
Current PSA version remains 1.2.0-psa01 / Build 46. Previous PSA IPv4 selection, password visibility, hotspot summary, disconnect button and manual hotspot flow remain intact.
Local AndroidPlay source commit: 10bd634c22071a2599c2cfd0e1325a711eb41549.
Remote build workflow commit: ad3d43ef0e3111503b198ebfa60774b702ae2ca9.
Branch: psa/androidplay-1.2.0-ipv4 in z892137292/psa-CarPlay. Formal main baseline was not changed.

## Actual changes
- AndroidPlay mobile/build.gradle.kts (delivered as androidplay-psa/patches/0003-Verify-standalone-authentication-packaging.patch): assembleStandaloneDebug now requires final debug APK verification. Both offline-mfi assets must be nonempty and exactly match the selected local inputs.
- .github/workflows/build-androidplay-psa.yml: no source-only fallback; require provisioned approved inputs, clean stale outputs, run unchanged local identity loader, unit tests and lint, assembleStandaloneDebug, verify final ZIP contents/arm64/package/version/minSdk/signature/SHA-256. Authenticated APK upload remains gated on separately confirmed redistribution authorization.
- This report. No Bluetooth, authentication protocol, AirPlay, USB, decoder, Surface, Activity, audio, touch or UI code changed.

## Environment findings
ANDROIDPLAY_AUTH_ASSETS_DIR is not set in the available local environment. The default AndroidPlay runtime-assets directory and both required resource files are absent. Signing environment is also not configured locally.
CI did not satisfy the combined credentials/use-authorization configuration gate. It does not reveal which individual secret or variable is absent.
No third-party APK private key was extracted. No credential, signing key or password was committed.
DiPlay experimental identity redistribution authorization has not been established; its public APK availability and code license are insufficient proof.

## Verification evidence
GitHub Actions run: https://github.com/z892137292/psa-CarPlay/actions/runs/37872462719
- Existing PSA patches applied successfully.
- Updated Gradle Kotlin DSL and task configuration: PASS, BUILD SUCCESSFUL in 57s.
- Authorized runtime authentication input gate: BLOCKED; run failed deliberately.
- New loader validation, unit tests, lint, APK assembly and final APK checks: SKIPPED.
- Local source diff check: PASS; only mobile/build.gradle.kts differs from the previous PSA source commit.
- Workflow YAML and embedded shell syntax checks: PASS.
Earlier 262 unit tests and lint results belong to the prior source-only build and are not new authenticated APK validation.

## Missing deliverables
No newly generated APK, APK SHA-256 or signing-certificate fingerprint exists for this attempt. The previously delivered SOURCE-ONLY / NO-CARPLAY-AUTH APK must not be relabeled as connection-capable.

## Resume and installation
Provide independently authorized matching offline-mfi/identity.pk8 and offline-mfi/certificate.p7b in a private build input directory; ANDROIDPLAY_AUTH_ASSETS_DIR points to the parent of offline-mfi. Do not commit these files.
For existing CI, configure its private authentication secrets and actual authorization record; public redistribution requires separate permission.
Then use the existing wrapper task :mobile:assembleStandaloneDebug. Before delivery require original loader parsing/key-certificate matching, final APK exact resource comparison, package/version/API28/CPU validation, signature verification and SHA-256.
Compare the new signer with the user's installed APK before claiming overwrite installation is possible. A mismatch prevents normal overwrite; do not instruct uninstall without user consent.

## Physical PSA acceptance
User must verify authentication no longer reports missing files, RFCOMM/iAP2/MFi, ap0 IPv4 AirPlay TCP/session, actual CarPlay display, lifecycle stability, audio/touch and disconnect/reconnect. Require three reconnect rounds, 15 minutes of stable display, screen photo/video and corresponding logs. First-frame logs alone are insufficient.

## Rollback
The original successful baseline and previous PSA source commits remain unchanged. To undo this packaging repair, revert the build configuration/workflow commits only. Keep any authentication inputs private. No installation or device state was changed.
