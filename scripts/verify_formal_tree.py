#!/usr/bin/env python3
"""Fail builds if removed network creation paths reappear; preserve mandatory components."""
import pathlib, re, sys, xml.etree.ElementTree as ET
root=pathlib.Path(sys.argv[1])
forbidden=re.compile(r'WifiP2pManager|WifiP2pGroupManager|RootSoftApBackend|AndroidApiSoftApBackend|LocalOnlyHotspotManager|startLocalOnlyHotspot|startTethering|stopTethering|setWifiApEnabled|createGroup\s*\(')
for base in ('shared/src/main','common/src/main','mobile/src/main'):
    for path in (root/base).rglob('*'):
        if path.suffix in ('.kt','.java','.xml'):
            assert not forbidden.search(path.read_text()), f'Forbidden experiment: {path}'
for name in ('ManualHotspotManager','ExistingWifiManager','CarPlayVpnService','Ipv6NcmBridge','Iap2WiredControlClient','Iap2WirelessControlClient','NcmUsbBridge','Iap2UsbMuxHost','LocalMfiAuthenticationClient'):
    assert list(root.glob(f'**/{name}.kt')), f'Missing formal component: {name}'
for path in root.glob('**/src/main/AndroidManifest.xml'):ET.parse(path)
host=(root/'common/src/main/java/com/shilapi/xcertplay/CarPlayHostActivity.kt').read_text()
assert 'mainFirstFrameReady && SCREEN_TYPE_MAIN in activeScreenStreamTypes' in host
assert 'controllerGeneration != restartGeneration' in host
assert 'returnHomeAfterConfirmedLoss' in host
print('PASS: no network creation API/controller, required USB/wireless/MFi modules present, XML and FIRST_FRAME guard')
