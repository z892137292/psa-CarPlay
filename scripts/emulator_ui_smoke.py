#!/usr/bin/env python3
"""Installed APK checks with no iPhone; never inject a fake connection/first frame."""
import subprocess,time,re,xml.etree.ElementTree as E,json,atexit,struct
from pathlib import Path
OUT=Path('out/emulator-ui');OUT.mkdir(parents=True,exist_ok=True)
PKG='com.psa.carplay.dev'
def adb(*args):return subprocess.check_output(['adb',*args],text=True).strip()
def launch(page='home',host=False,cold=False):
 args=['shell','am','start','-W','-n',PKG+'/com.shilapi.xcertplay.'+('CarPlayHostActivity' if host else 'DiPlayActivity')]
 if cold:args+=['-f','0x10008000'] # NEW_TASK | CLEAR_TASK: cold start, not Android task restoration.
 if page is not None:args+=['--es','page',page]
 adb(*args)
 time.sleep(.7)
def dump():
 for attempt in range(4):
  adb('shell','rm','-f','/sdcard/psa-ui.xml')
  result=adb('shell','uiautomator','dump','/sdcard/psa-ui.xml')
  if 'dumped to:' not in result:
   print('UI dump not current: '+result);time.sleep(.5);continue
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
 adb('shell','screencap','-p','/sdcard/psa-ui.png');adb('pull','/sdcard/psa-ui.png',str(OUT/(name+'.png')))
 (OUT/(name+'.xml')).write_text(E.tostring(root,encoding='unicode'))
 if name in {'cold-home','phones','connection','settings-1920','diagnostics','connecting-no-phone','network-not-ready','network-failure'}:
  dimensions=struct.unpack('>II',(OUT/(name+'.png')).read_bytes()[16:24])
  assert dimensions==(1920,720),(name,'actual screenshot dimensions',dimensions)
 for text in required:assert any(text in s for s in texts),(name,text,texts)
 return texts
def scroll_to(text):
 for attempt in range(8):
  root=dump()
  if any(text in n.get('text','') for n in root.iter('node')):return
  scroll=next(n for n in root.iter('node') if n.get('scrollable')=='true')
  x1,y1,x2,y2=map(int,re.findall(r'\d+',scroll.get('bounds')))
  adb('shell','input','swipe',str((x1+x2)//2),str(y2-80),str((x1+x2)//2),str(y1+100),'500');time.sleep(.5)
 raise AssertionError('Cannot scroll to '+text)
def save_logcat():
 with (OUT/'logcat.txt').open('w') as f:subprocess.run(['adb','logcat','-d','-v','threadtime'],stdout=f,stderr=subprocess.DEVNULL)
atexit.register(save_logcat)
apk=next(Path('out').glob('*.apk'));adb('install','-r',str(apk))
for perm in ['RECORD_AUDIO','ACCESS_FINE_LOCATION','ACCESS_COARSE_LOCATION','WRITE_EXTERNAL_STORAGE']:
 subprocess.run(['adb','shell','pm','grant',PKG,'android.permission.'+perm],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
adb('shell','wm','size','1920x720');adb('shell','wm','density','160')
assert 'Override size: 1920x720' in adb('shell','wm','size'),'Emulator clamped requested head-unit dimensions'
# Android's first-use immersive tutorial obscures the app hierarchy; configure the test device.
adb('shell','settings','put','secure','immersive_mode_confirmations','confirmed')
adb('shell','am','force-stop',PKG);launch(None,cold=True)
texts=check('auto-cold-launch','PSA CarPlay')
assert any(t in texts for t in ['连接手机','取消连接']),'Automatic cold launch has no usable connection controls'
adb('shell','am','force-stop',PKG);launch('settings',cold=True);check('settings','PSA CarPlay','首选连接方式')
scroll_to('保持屏幕唤醒')
check('settings-scrolled','PSA CarPlay','保持屏幕唤醒')
# Stop automatic connection so the no-phone cold-start and each explicit retry are separate.
# This edits the same user preference as the UI toggle, using debuggable run-as.
xml='<map><boolean name="auto_connect" value="false" /></map>'
subprocess.run(['adb','shell','run-as',PKG,'sh','-c',"'mkdir -p shared_prefs; cat > shared_prefs/diplay.xml'"],input=xml,text=True,check=True)
adb('shell','am','force-stop',PKG);launch(cold=True);check('cold-home','PSA CarPlay','连接手机')
check('network-failure','车机热点未开启')
tap('手机');check('phones','未发现已配对')
tap('连接');check('connection','车机热点')
tap('诊断');check('diagnostics','连接诊断')
tap('设置');check('settings-1920','Wi-Fi 设置','车机热点设置')
tap('Wi-Fi 设置');time.sleep(1)
assert re.search(r'mResumedActivity[^\n]*WifiSettings',adb('shell','dumpsys','activity','activities')), 'Wi-Fi button did not resume WLAN settings'
check('wifi-settings-opened')
launch(cold=True)
tap('连接');check('connection-return','车机热点')
tap('CarPlay');tap('连接手机');check('connecting-no-phone','PSA CarPlay','取消连接')
time.sleep(2);check('network-not-ready','取消连接')
for i in range(10):
 tap('取消连接');time.sleep(1)
 launch();check('retry-home-'+str(i),'连接手机')
 tap('连接手机');check('retry-loading-'+str(i),'取消连接')
adb('shell','wm','size','720x1920');time.sleep(1);check('portrait','PSA CarPlay','取消连接')
adb('shell','wm','size','1920x720');time.sleep(1);check('landscape-restored','PSA CarPlay','取消连接')
adb('shell','input','keyevent','3');launch(host=True);check('foreground-no-frame','取消连接')
# Grant only the emulator's real VPN prerequisite; no USB device/session is injected.
adb('shell','appops','set',PKG,'ACTIVATE_VPN','allow')
adb('shell','am','force-stop',PKG);launch('connection',cold=True);tap('USB CarPlay');tap('CarPlay');tap('连接手机');check('usb-absent','PSA CarPlay','取消连接')
log=adb('logcat','-d','-v','threadtime');(OUT/'logcat.txt').write_text(log)
assert not re.search(r'FATAL EXCEPTION[^\n]*\n(?:[^\n]*\n){0,3}[^\n]*Process: '+re.escape(PKG),log)
(OUT/'RESULT.json').write_text(json.dumps({'installed_apk':apk.name,'cold_launch':True,'no_phone_ui':True,'paired_list_empty_state':True,'connect_cancel_cycles':10,'usb_absent':True,'orientation':True,'first_frame_hardware_test':'NOT_PERFORMED: no iPhone'},indent=2))
print('PASS: installed Android 9 UI cold launch, real empty Bluetooth list, no-phone connection, 10 cancel/retry cycles, USB absent, orientation and foreground')
