#!/usr/bin/env python3
"""Byte-level ZIP/DEX/manifest scope checks. Pair with apksigner and ART/vehicle tests."""
import hashlib,json,pathlib,struct,sys,zipfile,zlib
mother,test=map(pathlib.Path,sys.argv[1:3])
assert hashlib.sha256(mother.read_bytes()).hexdigest()=='968c4c2bf8aa9187ae4cd619cb59c4eaf1e4792f0ba002d773cebdf38ca2c311'
with zipfile.ZipFile(mother) as a, zipfile.ZipFile(test) as b:
    assert a.testzip() is None and b.testzip() is None
    assert len(b.namelist())==len(set(b.namelist()))
    assert set(a.namelist())==set(b.namelist()),'Entry additions/removals forbidden'
    changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
    assert set(changed)=={'classes3.dex'},changed
    dex=[]
    for name in sorted(n for n in b.namelist() if n.endswith('.dex')):
        data=b.read(name)
        assert data[:4]==b'dex\n' and data[7]==0
        assert struct.unpack_from('<I',data,32)[0]==len(data)
        assert struct.unpack_from('<I',data,8)[0]==zlib.adler32(data[12:])&0xffffffff
        assert data[12:32]==hashlib.sha1(data[32:]).digest()
        assert struct.unpack_from('<I',data,36)[0]==112
        assert struct.unpack_from('<I',data,40)[0]==0x12345678
        for off,width in [(56,4),(64,4),(72,12),(80,8),(88,8),(96,32)]:
            count,start=struct.unpack_from('<II',data,off)
            assert start+count*width<=len(data)
        dex.append({'name':name,'size':len(data),'classes':struct.unpack_from('<I',data,96)[0],
                    'sha256':hashlib.sha256(data).hexdigest(),'checksums':'PASS'})
    report={'mother_sha256':hashlib.sha256(mother.read_bytes()).hexdigest(),
            'test_sha256':hashlib.sha256(test.read_bytes()).hexdigest(),
            'test_size':test.stat().st_size,'zip_entries':len(b.namelist()),
            'changed_entries':changed,'unchanged_entries':len(b.namelist())-len(changed),
            'manifest_resources_native_libraries_and_auth_assets':'BYTE_IDENTICAL',
            'dex':dex,'runtime_validation':'NOT RUN'}
print(json.dumps(report,indent=2))
