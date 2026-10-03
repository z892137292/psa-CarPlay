# PSA CarPlay

PSA Android 9 / API 28 CarPlay test build based on DiPlay v0.2.10.

This repository intentionally does **not** store accessory identity files, Android signing keys, or other credentials.

## PSA Test 0.1

Build strategy:

1. Fetch the official DiPlay v0.2.10 source tag.
2. Apply the PSA Test 0.1 patch.
3. Fetch the official DiPlay v0.2.10 APK only during CI and extract its two runtime `offline-mfi` assets into the temporary GitHub Actions runner.
4. Build `:mobile:assembleStandaloneDebug`.
5. Upload the installable APK as a GitHub Actions artifact.

Target: Android 9 / API 28 PSA head unit.

The first test build keeps the working DiPlay CarPlay core, disables BYD-specific runtime integrations, and adds disconnect diagnostics. Service refactoring and NCM recovery are intentionally deferred until the first PSA disconnect log is captured.
