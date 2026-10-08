#!/usr/bin/env python3
"""PSA ROM compatibility source guard. Hardware success is not inferred from this check."""
import pathlib, re, json, hashlib, sys
root = pathlib.Path(sys.argv[1])
audio = (root/'shared/src/main/java/com/shilapi/xcertplay/media/AndroidMediaSink.kt').read_text()
code = re.sub(r'/\*.*?\*/|//[^\n]*', '', audio, flags=re.S)
assert not re.search(r'\bgetAudioAttributes\s*\(|\b(?:built|track|currentTrack)\s*\??\.\s*audioAttributes\b', code), 'ROM-incompatible AudioTrack attribute getter'
assert 'trackAttributes = attributes' in code and 'trackAttributes = fallbackAttributes' in code
assert 'RomAudioGuard.requireInitialized' in code and 'RomAudioGuard.initialize' in code
assert 'catch (error: LinkageError)' in code
for item in json.loads((pathlib.Path(__file__).parent.parent/'docs/evidence/PSA_PRESERVED_SOURCE_SHA256.json').read_text()):
    assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest() == item['sha256'], 'Unexpected protocol/USB change: '+item['path']
assert 'minSdk = 28' in (root/'mobile/build.gradle.kts').read_text()
print('PASS: ROM getter absent; actual attributes/fallback retained; audio initialization guarded; USB/Bluetooth/MFi/AirPlay/manual hotspot baseline bytes preserved; minSdk=28')
