#!/usr/bin/env python3
"""Build locally from the sole pinned mother. Never uploads APKs or reads key contents."""
import argparse
import hashlib
import pathlib
import re
import subprocess
import sys
import zipfile

EXPECTED = '6e5f6c0ab10d16c2abaef6d00eda0e7c0a76d78c7eef55c942e8a0338ce83d5e'
p = argparse.ArgumentParser()
p.add_argument('--mother', required=True, type=pathlib.Path)
p.add_argument('--apktool', required=True, type=pathlib.Path)
p.add_argument('--build-tools', required=True, type=pathlib.Path)
p.add_argument('--jdk', required=True, type=pathlib.Path)
p.add_argument('--work', required=True, type=pathlib.Path)
p.add_argument('--keystore', required=True, type=pathlib.Path)
p.add_argument('--password-file', required=True, type=pathlib.Path)
p.add_argument('--alias', default='psa-media-test')
p.add_argument('--output', required=True, type=pathlib.Path)
a = p.parse_args()
for name in ['mother','apktool','build_tools','jdk','work','keystore','password_file','output']:
    setattr(a,name,getattr(a,name).resolve())
if hashlib.sha256(a.mother.read_bytes()).hexdigest() != EXPECTED:
    raise SystemExit('STOP: mother SHA-256 mismatch')
if hashlib.sha256(a.apktool.read_bytes()).hexdigest() != '66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa':
    raise SystemExit('STOP: use the pinned Apktool 2.12.1 binary from README')
if a.output == a.mother or a.output.exists():
    raise SystemExit('STOP: output exists or is mother; choose a new output path')
a.work.mkdir(parents=True, exist_ok=False)
a.output.parent.mkdir(parents=True, exist_ok=True)
source = pathlib.Path(__file__).resolve().parents[1]
classes = a.work/'tool-classes'; classes.mkdir()
def run(*args, **kw):
    subprocess.run(list(map(str,args)),check=True,**kw)
run(a.jdk/'bin/javac','-cp',a.apktool,'-d',classes,source/'scripts/SmaliTool.java')
classpath = str(classes)+':'+str(a.apktool)
def smali(mode, source, target):
    run(a.jdk/'bin/java','-cp',classpath,'SmaliTool',mode,source,target)
with zipfile.ZipFile(a.mother) as mother:
    if mother.testzip() is not None: raise SystemExit('Corrupt mother ZIP')
    (a.work/'original.dex').write_bytes(mother.read('classes3.dex'))
    (a.work/'original8.dex').write_bytes(mother.read('classes8.dex'))
smali('disassemble',a.work/'original.dex',a.work/'smali_classes3')
smali('disassemble',a.work/'original8.dex',a.work/'smali_classes8')
with (source/'media-ipv4-fix.patch').open('rb') as patch:
    run('patch','--batch','--fuzz=0','-p1',cwd=a.work,stdin=patch)
smali('assemble',a.work/'smali_classes3',a.work/'classes3.dex')
smali('assemble',a.work/'smali_classes8',a.work/'classes8.dex')
unsigned=a.work/'unsigned.apk'
with zipfile.ZipFile(a.mother) as mother, zipfile.ZipFile(unsigned,'w') as out:
    for entry in mother.infolist():
        # Remove only JAR signing records; all unrelated META-INF data is preserved.
        if re.fullmatch(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))',entry.filename,re.I): continue
        data=(a.work/entry.filename).read_bytes() if entry.filename in ('classes3.dex','classes8.dex') else mother.read(entry)
        out.writestr(entry,data)
aligned=a.work/'aligned.apk'
run(a.build_tools/'zipalign','-P','16','-f','4',unsigned,aligned)
run(a.build_tools/'apksigner','sign','--ks',a.keystore,'--ks-key-alias',a.alias,
    '--ks-pass','file:'+str(a.password_file),
    '--v1-signing-enabled','false','--v2-signing-enabled','true','--v3-signing-enabled','true',
    '--v4-signing-enabled','false','--out',a.output,aligned)
run(a.build_tools/'apksigner','verify','--verbose','--print-certs',a.output)
run(a.build_tools/'zipalign','-c','-P','16','4',a.output)
with (a.work/'apk-verification.json').open('w') as report:
    run(sys.executable,source/'scripts/verify_apk.py',a.mother,a.output,stdout=report)
if hashlib.sha256(a.mother.read_bytes()).hexdigest()!=EXPECTED: raise SystemExit('Mother changed')
print('OUTPUT SHA256',hashlib.sha256(a.output.read_bytes()).hexdigest())
print('STRUCTURE/SIGNATURE CHECK ONLY; NOT ART/INSTALLATION/PSA VALIDATION.')
