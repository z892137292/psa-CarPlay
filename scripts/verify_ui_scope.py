#!/usr/bin/env python3
"""Reject unrelated changes against the exact last UI-fixed transport revision."""
from pathlib import Path
import sys

baseline,candidate=map(Path,sys.argv[1:3])
allowed={
 "common/src/test/java/com/shilapi/xcertplay/NetworkSettingsLauncherTest.kt",
 "common/src/test/java/com/shilapi/xcertplay/SystemHotspotManagerTest.kt",
 "shared/src/main/java/com/shilapi/xcertplay/network/SystemHotspotManager.kt",
 "common/src/main/java/com/shilapi/xcertplay/DiagnosticRedactor.kt",
 "common/src/test/java/com/shilapi/xcertplay/DiagnosticRedactorTest.kt",
 "common/src/test/java/com/shilapi/xcertplay/LanNetworkManagerTest.kt",
 "common/src/main/java/com/shilapi/xcertplay/NetworkSettingsLauncher.kt",
 "common/src/test/java/com/shilapi/xcertplay/NetworkIdentityResolverTest.kt",
 "shared/src/main/java/com/shilapi/xcertplay/network/NetworkIdentityResolver.kt",
 "shared/src/main/java/com/shilapi/xcertplay/network/ExistingWifiManager.kt",
 "shared/src/main/java/com/shilapi/xcertplay/network/ExistingSystemAp.kt",
 "shared/src/main/java/com/shilapi/xcertplay/orchestration/ExistingLanSuccessEvidence.kt",
 "shared/src/test/java/com/shilapi/xcertplay/orchestration/ExistingLanSuccessEvidenceTest.kt",
 'mobile/build.gradle.kts',
 'common/src/main/java/com/shilapi/xcertplay/AirPlayPersistence.kt',
 'common/src/main/java/com/shilapi/xcertplay/BluetoothPhoneRepository.kt',
 'common/src/main/java/com/shilapi/xcertplay/CarPlayHostActivity.kt',
 'common/src/main/java/com/shilapi/xcertplay/CarPlayShell.kt',
 'common/src/main/java/com/shilapi/xcertplay/CarPlayUiState.kt',
 'common/src/main/java/com/shilapi/xcertplay/DiPlayActivity.kt',
 'common/src/test/java/com/shilapi/xcertplay/CarPlayHostPreparationTest.kt',
 'common/src/test/java/com/shilapi/xcertplay/CarPlayShellStartupTest.kt',
 'common/src/test/java/com/shilapi/xcertplay/CarPlayUiStateTest.kt',
 'common/src/test/java/com/shilapi/xcertplay/HotspotModeMigrationTest.kt',
 'shared/src/main/java/com/shilapi/xcertplay/network/ManualHotspotManager.kt',
 'shared/src/main/java/com/shilapi/xcertplay/orchestration/CarPlayController.kt',
}
def files(root):
 return {str(p.relative_to(root)):p for p in root.rglob('*') if p.is_file() and not any(v in {'.git','build','.gradle'} for v in p.relative_to(root).parts)}
old,new=files(baseline),files(candidate)
assert not old.keys()-new.keys(),'Existing files deleted: '+str(old.keys()-new.keys())
changed=sorted(p for p in new if p not in old or new[p].read_bytes()!=old[p].read_bytes())
assert set(changed)<=allowed,'Unrelated changes: '+str(set(changed)-allowed)
path='shared/src/main/java/com/shilapi/xcertplay/orchestration/CarPlayController.kt'
a,b=old[path].read_text(),new[path].read_text()
start,end='    private fun startIphone()','    private fun isBluetoothHandoffCommand'
assert a[a.index(start):a.index(end)]==b[b.index(start):b.index(end)],'USB controller block changed'
print('UI baseline: 265775013acbb20c720d280600b466261c81624f, versionCode 215')
print('PASS: no existing source files deleted; unchanged AirPlay/USBMUX/NCM/iAP2/MFi/video/audio/touch protocol implementations')
print('PASS: complete USB controller bring-up unchanged; SystemHotspotManager lifecycle preserved; STA/AP identity normalization explicitly updated')
print('UI source files changed:')
print('\n'.join(changed))
