package com.psa.hotspothelper;
import android.Manifest;
import android.app.*;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.location.LocationManager;
import android.provider.Settings;
import android.graphics.Color;
import android.view.*;
import android.widget.*;

public class P2pTestActivity extends Activity {
 private final Handler handler=new Handler(Looper.getMainLooper());private TextView display;private boolean resumed;
 private final Runnable refresh=new Runnable(){public void run(){if(resumed){render();handler.postDelayed(this,1000);}}};
 private int dp(int n){return (int)(getResources().getDisplayMetrics().density*n+.5f);}
 @Override public void onCreate(Bundle b){super.onCreate(b);getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
  ScrollView sc=new ScrollView(this);sc.setBackgroundColor(Color.parseColor("#0D1622"));LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(24),dp(12),dp(24),dp(12));sc.addView(root);
  TextView title=new TextView(this);title.setText("PSA Hotspot · Wi-Fi Direct 测试");title.setTextSize(24);title.setTextColor(Color.WHITE);root.addView(title);
  display=new TextView(this);display.setTextColor(Color.parseColor("#56D8DD"));display.setTextSize(17);display.setPadding(0,dp(12),0,dp(12));root.addView(display);
  LinearLayout row=new LinearLayout(this);root.addView(row);String[] labels={"创建测试网络","停止测试","检测状态","查看日志","返回热点页"};
  for(int i=0;i<labels.length;i++){final int index=i;Button bt=new Button(this);bt.setText(labels[i]);bt.setTextSize(16);row.addView(bt,new LinearLayout.LayoutParams(0,dp(72),1));bt.setOnClickListener(v->{if(index==0)startTest();else if(index==1)command("STOP");else if(index==2)render();else if(index==3)logs();else finish();});}
  TextView help=new TextView(this);help.setText("先在空闲时测试：开启车机 Wi-Fi 和定位、允许定位权限；原热点请手动关闭以减少冲突。创建成功后，用 iPhone 设置里的 Wi-Fi 尝试加入显示的网络。此页只验证网络，不会建立 CarPlay，也不会共享移动流量。\n测试由前台服务保持，结束请点“停止测试”；系统杀进程后不会自动接管残留网络。密码只在此页显示，不写入日志。");help.setTextColor(Color.LTGRAY);help.setTextSize(14);root.addView(help);setContentView(sc);render();
 }
 private void render(){LocationManager lm=getSystemService(LocationManager.class);boolean location=lm!=null&&lm.isLocationEnabled();boolean feature=getPackageManager().hasSystemFeature(PackageManager.FEATURE_WIFI_DIRECT);
  display.setText("系统：Android API "+Build.VERSION.SDK_INT+" · P2P硬件声明："+(feature?"支持":"不支持")+"\n定位开关："+(location?"已开启":"未开启")+" · 定位权限："+(checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED?"已授权":"未授权")+"\n状态："+P2pTestService.status+"\n"+P2pTestService.details+"\n接入密码："+(P2pTestService.password.isEmpty()?"未获取":P2pTestService.password));}
 private void startTest(){if(checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION},7);return;}LocationManager lm=getSystemService(LocationManager.class);if(lm==null||!lm.isLocationEnabled()){new AlertDialog.Builder(this).setMessage("请先开启系统定位，再创建测试网络。用于系统Wi-Fi权限检查，应用不读取定位坐标。").setPositiveButton("定位设置",(d,w)->{try{startActivity(new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS));}catch(RuntimeException e){Toast.makeText(this,"定位设置入口不可用",0).show();}}).setNegativeButton("返回",null).show();return;}command("CREATE");}
 private void command(String action){try{startForegroundService(new Intent(this,P2pTestService.class).setAction(action));}catch(RuntimeException e){Toast.makeText(this,"服务启动失败："+e.getClass().getSimpleName(),Toast.LENGTH_LONG).show();}}
 @Override public void onRequestPermissionsResult(int code,String[] names,int[] results){super.onRequestPermissionsResult(code,names,results);if(code==7&&results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED)startTest();}
 private void logs(){String text=getSharedPreferences("p2p",0).getString("logs","暂无P2P日志");TextView tv=new TextView(this);tv.setText(text);tv.setTextIsSelectable(true);tv.setPadding(dp(16),dp(12),dp(16),dp(12));ScrollView sc=new ScrollView(this);sc.addView(tv);new AlertDialog.Builder(this).setTitle("P2P日志（不含密码）").setView(sc).setPositiveButton("关闭",null).setNeutralButton("复制",(d,w)->((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("P2P日志",text))).show();}
 @Override protected void onResume(){super.onResume();resumed=true;handler.post(refresh);}
 @Override protected void onPause(){resumed=false;handler.removeCallbacks(refresh);super.onPause();}
}
