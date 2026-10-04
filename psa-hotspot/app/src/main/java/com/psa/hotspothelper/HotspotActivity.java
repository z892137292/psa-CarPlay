package com.psa.hotspothelper;

import android.app.*;
import android.os.*;
import android.content.*;
import android.net.ConnectivityManager;
import android.net.wifi.WifiManager;
import android.provider.Settings;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.*;
import android.widget.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;

public class HotspotActivity extends Activity {
 private final Handler handler = new Handler(Looper.getMainLooper());
 private final ExecutorService worker = Executors.newSingleThreadExecutor();
 private final ArrayList<String> logs = new ArrayList<>();
 private final TextView[] values = new TextView[4];
 private TextView summary, note;
 private boolean active; private int generation; private String previous = "";
 private final Runnable poll = new Runnable() { public void run() { if(active){ detect(); handler.postDelayed(this,3000); } } };
 private int dp(int n){return (int)(getResources().getDisplayMetrics().density*n+.5f);}
 private GradientDrawable bg(String color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(Color.parseColor(color));d.setCornerRadius(dp(radius));return d;}
 private TextView text(String s,int size,String color){TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(Color.parseColor(color));return t;}
 @Override public void onCreate(Bundle b){super.onCreate(b);
  String saved=getPreferences(0).getString("logs",""); for(String line:saved.split("\n"))if(!line.isEmpty())logs.add(line);
  ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(Color.parseColor("#0D1622"));
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(24),dp(14),dp(24),dp(14));scroll.addView(root);
  TextView title=text("PSA Hotspot",28,"#F2F6FC");title.setTypeface(null,Typeface.BOLD);root.addView(title);
  summary=text("状态检测中",17,"#56D8DD");root.addView(summary);
  LinearLayout body=new LinearLayout(this);body.setPadding(0,dp(12),0,dp(10));root.addView(body,new LinearLayout.LayoutParams(-1,0,1));
  LinearLayout left=new LinearLayout(this);left.setOrientation(1);body.addView(left,new LinearLayout.LayoutParams(0,-2,1.1f));
  String[] names={"热点名称","热点 IP","热点状态","连接设备"};
  for(int i=0;i<4;i++){LinearLayout row=new LinearLayout(this);row.setOrientation(1);row.setPadding(dp(14),dp(7),dp(14),dp(7));row.setBackground(bg("#192838",10));LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,-2);rp.bottomMargin=dp(7);left.addView(row,rp);row.addView(text(names[i],13,"#9CAFC3"));values[i]=text("待检测",18,"#F2F6FC");row.addView(values[i]);}
  LinearLayout right=new LinearLayout(this);right.setOrientation(1);right.setPadding(dp(18),0,0,0);body.addView(right,new LinearLayout.LayoutParams(0,-1,1));
  String[] labels={"开启热点","关闭热点","检测连接","查看日志"};
  for(int r=0;r<2;r++){LinearLayout row=new LinearLayout(this);right.addView(row,new LinearLayout.LayoutParams(-1,0,1));for(int c=0;c<2;c++){final int n=r*2+c;Button button=new Button(this);button.setText(labels[n]);button.setTextSize(19);button.setAllCaps(false);button.setTextColor(Color.WHITE);button.setBackground(bg(n==0?"#147E88":"#28435E",12));LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-1,1);p.setMargins(dp(5),dp(5),dp(5),dp(5));row.addView(button,p);button.setOnClickListener(v->{if(n<2)settings(n==0);else if(n==2){log("手动检测连接");detect();}else showLogs();});}}
  note=text("v0.2 · 开关进入系统设置，由你手动操作；无法读取的信息显示未知。",13,"#A5B4C6");root.addView(note);Button p2p=new Button(this);p2p.setText("Wi-Fi Direct 测试");p2p.setOnClickListener(v->startActivity(new Intent(this,P2pTestActivity.class)));root.addView(p2p);setContentView(scroll);log("PSA Hotspot v0.2 启动 · Android API "+Build.VERSION.SDK_INT);
 }
 @Override protected void onResume(){super.onResume();active=true;generation++;handler.post(poll);}
 @Override protected void onPause(){active=false;generation++;handler.removeCallbacks(poll);super.onPause();}
 @Override protected void onDestroy(){worker.shutdownNow();super.onDestroy();}
 private Object call(Object object,String method)throws Exception{return object.getClass().getMethod(method).invoke(object);}
 private void detect(){if(!active)return;final int token=generation;worker.execute(()->{
  String[] result={"系统未开放读取","无法确认热点接口","未知（系统未开放）","未知（系统未开放）"};String detail="";
  WifiManager wifi=(WifiManager)getApplicationContext().getSystemService(WIFI_SERVICE);int state=-1;
  try{state=((Number)call(wifi,"getWifiApState")).intValue();}catch(Exception e){detail="热点状态接口不可用："+e.getClass().getSimpleName();try{state=(Boolean)call(wifi,"isWifiApEnabled")?13:11;}catch(Exception ignored){}}
  String[] states={"关闭中","已关闭","开启中","已开启","开启失败"};if(state>=10&&state<=14)result[2]=states[state-10];
  try{Object config=call(wifi,"getWifiApConfiguration");if(config!=null){Object ssid=config.getClass().getField("SSID").get(config);if(ssid instanceof String&&!((String)ssid).isEmpty())result[0]=(String)ssid;}}catch(Exception ignored){}
  if(state==13){try{ConnectivityManager cm=(ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);String[] interfaces=(String[])call(cm,"getTetheredIfaces");String[] wifiPatterns=(String[])call(cm,"getTetherableWifiRegexs");ArrayList<String> ips=new ArrayList<>();for(String name:interfaces){boolean isWifi=false;for(String pattern:wifiPatterns)if(name.matches(pattern))isWifi=true;if(!isWifi)continue;NetworkInterface ni=NetworkInterface.getByName(name);if(ni==null)continue;for(InetAddress address:Collections.list(ni.getInetAddresses()))if(address instanceof Inet4Address&&!address.isLoopbackAddress())ips.add(name+": "+address.getHostAddress());}if(!ips.isEmpty())result[1]=String.join("\n",ips);}catch(Exception ignored){}
   for(String method:new String[]{"getHotspotClients","getWifiApConnectedStations"})try{Object clients=call(wifi,method);if(clients instanceof Collection){result[3]="系统报告 "+((Collection<?>)clients).size()+" 台（未验证身份）";break;}}catch(Exception ignored){}
  }else if(state==11){result[1]="热点已关闭";result[3]="热点已关闭";}
  final String diagnostic=detail;handler.post(()->{if(!active||token!=generation)return;for(int i=0;i<4;i++)values[i].setText(result[i]);summary.setText("热点："+result[2]+" · 每 3 秒检测");String snapshot=Arrays.toString(result)+diagnostic;if(!snapshot.equals(previous)){previous=snapshot;log("检测："+result[2]+"；IP："+result[1]+"；设备："+result[3]+(diagnostic.isEmpty()?"":"；"+diagnostic));}});
 });}
 private void settings(boolean enable){String operation=enable?"开启":"关闭";note.setText("请在系统热点设置中手动"+operation+"热点，返回后自动重新检测。");Toast.makeText(this,"请在系统设置中手动"+operation+"热点",Toast.LENGTH_LONG).show();
  Intent[] candidates={new Intent("com.android.settings.WIFI_TETHER_SETTINGS"),new Intent("android.settings.TETHER_SETTINGS"),new Intent().setClassName("com.android.settings","com.android.settings.Settings$WifiTetherSettingsActivity"),new Intent().setClassName("com.android.settings","com.android.settings.Settings$TetherSettingsActivity")};
  for(Intent intent:candidates)try{startActivity(intent);log("已打开设置入口："+(intent.getComponent()==null?intent.getAction():intent.getComponent().getClassName()));return;}catch(ActivityNotFoundException|SecurityException e){log("设置入口不可用："+(intent.getComponent()==null?intent.getAction():intent.getComponent().getClassName())+" / "+e.getClass().getSimpleName());}
  new AlertDialog.Builder(this).setTitle("热点页面入口暂不可用").setMessage("可进入网络设置或系统设置查找热点；日志已记录尝试的入口。").setPositiveButton("网络设置",(d,w)->fallback(Settings.ACTION_WIRELESS_SETTINGS)).setNeutralButton("系统设置",(d,w)->fallback(Settings.ACTION_SETTINGS)).setNegativeButton("返回",null).show();
 }
 private void fallback(String action){try{startActivity(new Intent(action));log("打开备用设置："+action);}catch(ActivityNotFoundException|SecurityException e){log("备用设置不可用："+e.getClass().getSimpleName());Toast.makeText(this,"系统未开放此设置入口",Toast.LENGTH_LONG).show();}}
 private void log(String s){logs.add(new java.text.SimpleDateFormat("MM-dd HH:mm:ss",Locale.CHINA).format(new Date())+" "+s);while(logs.size()>200)logs.remove(0);getPreferences(0).edit().putString("logs",String.join("\n",logs)).apply();}
 private void showLogs(){ScrollView sc=new ScrollView(this);TextView t=text(String.join("\n",logs),14,"#E0E9F4");t.setPadding(dp(16),dp(12),dp(16),dp(12));t.setTextIsSelectable(true);sc.addView(t);new AlertDialog.Builder(this).setTitle("检测日志（最近 200 条）").setView(sc).setPositiveButton("关闭",null).setNeutralButton("复制",(d,w)->{((android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("PSA Hotspot 日志",String.join("\n",logs)));}).setNegativeButton("清空",(d,w)->{logs.clear();getPreferences(0).edit().remove("logs").apply();}).show();}
}
