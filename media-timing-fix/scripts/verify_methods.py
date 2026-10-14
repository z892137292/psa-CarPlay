#!/usr/bin/env python3
"""Compare disassemblies made with the same pinned SmaliTool. Fail outside timing methods."""
import pathlib,re,json,sys
b,a=map(pathlib.Path,sys.argv[1:3])
bs={str(p.relative_to(b)):p for p in b.rglob('*.smali')}
aa={str(p.relative_to(a)):p for p in a.rglob('*.smali')}
assert bs and bs.keys()==aa.keys()
pattern=r'^\.method ([^\n]+)\n.*?^\.end method'
changes=[];total=0
for n,p in bs.items():
    x=p.read_text();y=aa[n].read_text()
    methods=lambda s:{m.group(1):m.group(0) for m in re.finditer(pattern,s,re.M|re.S)}
    xx,yy=methods(x),methods(y)
    assert xx.keys()==yy.keys(),n
    assert re.sub(pattern,'',x,flags=re.M|re.S)==re.sub(pattern,'',y,flags=re.M|re.S),n
    total+=len(xx)
    changes.extend([n,m] for m in xx if xx[m]!=yy[m])
expected=[['com/shilapi/xcertplay/PsaMediaControl.smali','private refreshActive()V'],['com/shilapi/xcertplay/PsaMediaControl.smali','private restoreOnce()V']]
assert sorted(changes)==expected,changes
print(json.dumps({'classes_compared':len(bs),'methods_compared':total,'changed_methods':changes,'all_other_methods_fields_annotations':'IDENTICAL'},indent=2))
