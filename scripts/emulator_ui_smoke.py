#!/usr/bin/env python3
"""Installed APK checks with no iPhone; never inject a fake connection/first frame."""
import subprocess,time,re,xml.etree.ElementTree as E,json
from pathlib import Path
OUT=Path('out/emulator-ui');OUT.mkdir(parents=True,exist_ok=True)
PKG='com.psa.carplay.dev'
def adb(*args):return subprocess.check_output(['adb',*args],text=True).strip()
def launch(page='home',host=False):
 adb('shell','am','start','-W','-n',PKG+'/com.shilapi.xcertplay.'+('CarPlayHostActivity' if host else 'DiPlayActivity'),'--es','page',page)
 time.sleep(.7)
def dump():
 for attempt in range(4):
  adb('shell','uiautomator','dump','/sdcard/psa-ui.xml')
  xml=adb('shell','cat','/sdcard/psa-ui.xml')
  if xml.startswith('<?xml'):return E.fromstring(xml)
  time.sleep(.5)
 raise AssertionError('No UI hierarchy')
def tap(text):
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  root=dump()
  for node in root.iter('node'):
   if node.get('text')==text and node.get('enabled')=='true':
    x1,y1,x2,y2=map(int,re.findall(r'\d+',node.get('bounds')))
    if x2>x1 and y2>y1:
     adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2));time.sleep(.6);return
  time.sleep(.5)
 raise AssertionError('Missing/enabled button: '+text)
def check(name,*required):
 root=dump();texts=[n.get('text','') for n in root.iter('node')]
 for text in required:assert any(text in s for s in texts),(name,text,texts)
 adb('shell','screencap','-p','/sdcard/psa-ui.png');adb('pull','/sdcard/psa-ui.png',str(OUT/(name+'.png')))
 (OUT/(name+'.xml')).write_text(E.tostring(root,encoding='unicode'))
 return texts
apk=next(Path('out').glob('*.apk'));adb('install','-r',str(apk))
for perm in ['RECORD_AUDIO','ACCESS_FINE_LOCATION','ACCESS_COARSE_LOCATION','WRITE_EXTERNAL_STORAGE']:
 subprocess.run(['adb','shell','pm','grant',PKG,'android.permission.'+perm],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
adb('shell','wm','size','2250x1080');adb('shell','wm','density','160')
adb('shell','am','force-stop',PKG);launch('settings');check('settings','PSA CarPlay','系统')
# Stop automatic connection so the no-phone cold-start and each explicit retry are separate.
# This edits the same user preference as the UI toggle, using debuggable run-as.
xml='<map><boolean name="auto_connect" value="false" /></map>'
subprocess.run(['adb','shell','run-as',PKG,'sh','-c',"'mkdir -p shared_prefs; cat > shared_prefs/diplay.xml'"],input=xml,text=True,check=True)
adb('shell','am','force-stop',PKG);launch();check('cold-home','PSA CarPlay','连接手机')
tap('手机');check('phones','未发现已配对')
tap('连接');check('connection','车机热点')
tap('CarPlay');tap('连接手机');check('connecting-no-phone','PSA CarPlay','取消连接')
time.sleep(2);check('still-connecting-no-frame','取消连接')
for i in range(10):
 tap('取消连接');time.sleep(1)
 launch();check('retry-home-'+str(i),'连接手机')
 tap('连接手机');check('retry-loading-'+str(i),'取消连接')
adb('shell','wm','size','1080x2250');time.sleep(1);check('portrait','PSA CarPlay','取消连接')
adb('shell','wm','size','2250x1080');time.sleep(1);check('landscape-restored','PSA CarPlay','取消连接')
adb('shell','input','keyevent','3');launch(host=True);check('foreground-no-frame','取消连接')
adb('shell','am','force-stop',PKG);launch('connection');tap('USB CarPlay');tap('CarPlay');tap('连接手机');check('usb-absent','PSA CarPlay','取消连接')
log=adb('logcat','-d','-v','threadtime');(OUT/'logcat.txt').write_text(log)
assert not re.search(r'FATAL EXCEPTION.*\n.*'+re.escape(PKG),log)
(OUT/'RESULT.json').write_text(json.dumps({'installed_apk':apk.name,'cold_launch':True,'no_phone_ui':True,'paired_list_empty_state':True,'connect_cancel_cycles':10,'usb_absent':True,'orientation':True,'first_frame_hardware_test':'NOT_PERFORMED: no iPhone'},indent=2))
print('PASS: installed Android 9 UI cold launch, real empty Bluetooth list, no-phone connection, 10 cancel/retry cycles, USB absent, orientation and foreground')
