package com.psa.hotspothelper;

import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.net.wifi.p2p.*;
import android.os.*;
import java.net.*;
import java.util.*;

/** Owns only a group created and identified in this service lifetime. */
public class P2pTestService extends Service {
 public static String status="尚未测试", details="点击创建测试网络。", password="";
 private WifiP2pManager manager; private WifiP2pManager.Channel channel;
 private final Handler handler=new Handler(Looper.getMainLooper());
 private String ownedName, ownedInterface; private boolean starting, stopping, alive, createAccepted;
 private int generation; private long deadline;
 private final ArrayList<String> logs=new ArrayList<>();
 private final Runnable poll=new Runnable(){public void run(){if(alive&&!stopping){readGroup();handler.postDelayed(this,2000);}}};
 private final BroadcastReceiver receiver=new BroadcastReceiver(){public void onReceive(Context c,Intent i){if(WifiP2pManager.WIFI_P2P_STATE_CHANGED_ACTION.equals(i.getAction()))log("P2P状态："+(i.getIntExtra(WifiP2pManager.EXTRA_WIFI_STATE,-1)==WifiP2pManager.WIFI_P2P_STATE_ENABLED?"启用":"未启用"));readGroup();}};
 @Override public void onCreate(){super.onCreate();alive=true;
  for(String line:getSharedPreferences("p2p",0).getString("logs","").split("\n"))if(!line.isEmpty())logs.add(line);
  NotificationManager nm=getSystemService(NotificationManager.class);nm.createNotificationChannel(new NotificationChannel("p2p-test","Wi-Fi Direct 测试",NotificationManager.IMPORTANCE_LOW));
  PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,P2pTestActivity.class),PendingIntent.FLAG_IMMUTABLE);
  startForeground(2,new Notification.Builder(this,"p2p-test").setSmallIcon(com.psa.hotspothelper.R.drawable.ic_hotspot).setContentTitle("PSA Wi-Fi Direct 测试").setContentText("返回助手可查看或停止测试网络").setContentIntent(open).setOngoing(true).build());
  if(!getPackageManager().hasSystemFeature(PackageManager.FEATURE_WIFI_DIRECT)){fail("车机未声明支持 Wi-Fi Direct");return;}
  manager=getSystemService(WifiP2pManager.class);if(manager==null){fail("P2P服务不存在");return;}
  channel=manager.initialize(this,getMainLooper(),()->{channel=null;fail("P2P服务通道断开，无法确认网络状态");});
  IntentFilter filter=new IntentFilter();filter.addAction(WifiP2pManager.WIFI_P2P_STATE_CHANGED_ACTION);filter.addAction(WifiP2pManager.WIFI_P2P_CONNECTION_CHANGED_ACTION);
  registerReceiver(receiver,filter);handler.post(poll);log("P2P测试服务启动 · API "+Build.VERSION.SDK_INT);
 }
 @Override public int onStartCommand(Intent i,int flags,int id){if(i!=null&&manager!=null&&channel!=null){String action=i.getAction();if("CREATE".equals(action))create();else if("STOP".equals(action))stopOwned();else readGroup();}else if(i!=null&&"STOP".equals(i.getAction()))stopSelf();return START_NOT_STICKY;}
 private void create(){if(starting||stopping)return;if(ownedName!=null){status="本次测试网络已存在";return;}
  final int token=++generation;starting=true;createAccepted=false;status="检查已有P2P网络";deadline=SystemClock.elapsedRealtime()+20000;
  handler.postDelayed(()->{if(alive&&token==generation&&starting){starting=false;generation++;fail("建组超时，未继续重试或删除未知网络；请查看系统Wi-Fi状态");}},20000);
  try{manager.requestGroupInfo(channel,group->{if(!valid(token)||!starting)return;if(group!=null){starting=false;status="已有P2P网络，未接管";describe(group);log("发现已有P2P组，拒绝创建或删除");return;}
   status="正在创建，等待组信息";
   manager.createGroup(channel,new WifiP2pManager.ActionListener(){public void onSuccess(){if(valid(token)&&starting){createAccepted=true;log("系统已接受建组请求，尚未确认网络就绪");readGroup();}}public void onFailure(int reason){if(valid(token)){starting=false;fail("创建失败："+reason(reason));}}});
  });}catch(RuntimeException e){starting=false;fail("创建接口失败："+e.getClass().getSimpleName());}
 }
 private boolean valid(int token){return alive&&token==generation;}
 private void readGroup(){if(!alive||manager==null||channel==null||stopping)return;final int token=generation;
  try{manager.requestGroupInfo(channel,group->{if(!valid(token)||stopping)return;
   if(group==null){password="";details="当前未观察到P2P组；频段未知。";if(ownedName!=null){ownedName=null;ownedInterface=null;status="测试网络已断开";log(status);}else if(!starting)status="当前没有P2P网络";return;}
   if(starting&&createAccepted&&SystemClock.elapsedRealtime()<deadline){starting=false;if(group.isGroupOwner()&&group.getNetworkName()!=null&&group.getInterface()!=null){ownedName=group.getNetworkName();ownedInterface=group.getInterface();log("已观察到本次组主网络");}else {status="建组结果不是可确认的组主，未接管";describe(group);return;}}
   if(matches(group))status="测试网络已建立（未验证CarPlay）";else status="已有P2P网络（本服务不持有）";
   describe(group);
  });}catch(RuntimeException e){fail("读取组信息失败："+e.getClass().getSimpleName());}
 }
 private boolean matches(WifiP2pGroup g){return P2pOwnership.canRemove(ownedName,ownedInterface,g.isGroupOwner(),g.getNetworkName(),g.getInterface());}
 private void describe(WifiP2pGroup group){String iface=group.getInterface(),ip="未知";try{NetworkInterface ni=iface==null?null:NetworkInterface.getByName(iface);if(ni!=null){ArrayList<String> addresses=new ArrayList<>();for(InetAddress a:Collections.list(ni.getInetAddresses()))if(a instanceof Inet4Address&&!a.isLoopbackAddress())addresses.add(a.getHostAddress());if(!addresses.isEmpty())ip=String.join(", ",addresses);}}catch(Exception ignored){}
  String frequency="未知（Android 9不提供公开频率接口）";if(Build.VERSION.SDK_INT>=29)frequency=group.getFrequency()>0?group.getFrequency()+" MHz":"未知";
  password=matches(group)&&group.getPassphrase()!=null?group.getPassphrase():"";
  details="网络名称："+group.getNetworkName()+"\n本机组主："+(group.isGroupOwner()?"是":"否")+"\n接口："+iface+"\n接口 IPv4："+ip+"\n频率："+frequency+"\n系统报告P2P客户端："+group.getClientList().size()+"（可能不包含普通Wi-Fi接入，不能证明iPhone接入）";
 }
 private void stopOwned(){if(stopping)return;if(starting){status="建组过程中暂不能停止，请等待结果";return;}if(ownedName==null){status="没有可确认归属的测试网络，未删除任何组";log(status);stopSelf();return;}
  stopping=true;final int token=++generation;status="核验归属后停止测试";
  handler.postDelayed(()->{if(valid(token)&&stopping){stopping=false;status="停止超时，网络状态未知；可再次检查";log(status);}},10000);
  try{manager.requestGroupInfo(channel,group->{if(!valid(token)||!stopping)return;if(group==null){status="测试网络已不存在";stopSelf();return;}if(!matches(group)){stopping=false;ownedName=null;ownedInterface=null;status="网络归属已变化，拒绝删除";log(status);stopSelf();return;}
   manager.removeGroup(channel,new WifiP2pManager.ActionListener(){public void onSuccess(){if(valid(token)){status="系统已接受停止请求，正在核验";verifyStopped(token);}}public void onFailure(int code){if(valid(token)){stopping=false;fail("停止失败："+reason(code));}}});
  });}catch(RuntimeException e){stopping=false;fail("停止接口失败："+e.getClass().getSimpleName());}
 }
 private void verifyStopped(int token){if(!valid(token)||!stopping)return;try{manager.requestGroupInfo(channel,g->{if(!valid(token)||!stopping)return;if(g==null){status="测试网络已停止";details="本次测试组已移除。";password="";ownedName=null;ownedInterface=null;log(status);stopSelf();}else if(!matches(g)){status="本次组已消失，保留其他网络";ownedName=null;ownedInterface=null;log(status);stopSelf();}else handler.postDelayed(()->verifyStopped(token),500);});}catch(RuntimeException e){stopping=false;fail("停止核验失败："+e.getClass().getSimpleName());}}
 private String reason(int code){return code==WifiP2pManager.BUSY?"BUSY（系统忙）":code==WifiP2pManager.P2P_UNSUPPORTED?"P2P_UNSUPPORTED（系统不支持）":code==WifiP2pManager.ERROR?"ERROR（系统错误）":"代码 "+code;}
 private void fail(String message){status=message;log(message);}
 private void log(String s){logs.add(new java.text.SimpleDateFormat("MM-dd HH:mm:ss",Locale.CHINA).format(new Date())+" "+s);while(logs.size()>200)logs.remove(0);getSharedPreferences("p2p",0).edit().putString("logs",String.join("\n",logs)).apply();}
 @Override public void onDestroy(){alive=false;generation++;handler.removeCallbacksAndMessages(null);try{unregisterReceiver(receiver);}catch(Exception ignored){}if(channel!=null)channel.close();password="";super.onDestroy();}
 @Override public IBinder onBind(Intent i){return null;}
}
