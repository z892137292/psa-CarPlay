#!/usr/bin/env python3
import pathlib,sys
p=pathlib.Path(sys.argv[1])/'com/shilapi/xcertplay/PsaMediaControl.smali'
s=p.read_text()
old='    iget-boolean v0, p0, Lcom/shilapi/xcertplay/PsaMediaControl;->eligible:Z\n\n    if-eqz v0, :cond_3\n\n'
assert s.count(old)==1
s=s.replace(old,'')
old='    iget-boolean v0, p0, Lcom/shilapi/xcertplay/PsaMediaControl;->eligible:Z\n\n    if-eqz v0, :cond_0\n\n    const/4 v0, 0x1'
new='    iget-boolean v0, p0, Lcom/shilapi/xcertplay/PsaMediaControl;->foreground:Z\n\n    if-nez v0, :psa_ready\n\n'+old.replace('    const/4 v0, 0x1','    :psa_ready\n    const/4 v0, 0x1')
assert s.count(old)==1
p.write_text(s.replace(old,new))
