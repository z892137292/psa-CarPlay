import com.shilapi.xcertplay.PsaMediaControl;
import android.content.*;
import android.media.*;
import android.media.session.MediaSession;
import android.os.Handler;
import android.view.KeyEvent;
import java.util.*;

public final class MediaControlTest {
    static int assertions, scenarios;
    static void check(boolean b,String why){assertions++;if(!b)throw new AssertionError(why);}
    static final class Fixture {
        final AudioManager audio=new AudioManager(); final Handler handler=new Handler();
        final MediaSession session=new MediaSession(); final List<Integer> commands=new ArrayList<Integer>();
        final List<Long> seeks=new ArrayList<Long>(); int stops;
        final PsaMediaControl control;
        Fixture(){Context c=new Context();c.service=audio;control=PsaMediaControl.install(c,session,new MediaSession.Callback(){
            public void onPlay(){commands.add(1);} public void onPause(){commands.add(2);}
            public void onSkipToNext(){commands.add(4);} public void onSkipToPrevious(){commands.add(5);}
            public void onSeekTo(long p){seeks.add(p);} public void onStop(){stops++;}
        },handler);}
        void visible(boolean v){control.setForeground(v);handler.idle();}
        void start(){visible(true);control.update(true,true);}
        boolean key(int key,int action,int repeat,long time,int device){Intent i=new Intent();i.event=new KeyEvent(key,action,repeat,time,device);return session.callback.onMediaButtonEvent(i);}
    }
    static void run(String name,Runnable r){r.run();scenarios++;System.out.println("PASS "+name);}
    public static void main(String[] args){
        run("first connection restores before metadata",()->{Fixture f=new Fixture();f.visible(true);check(f.audio.requests==1 && f.session.active,"foreground restores BEFORE metadata or play");f.control.update(false,true);check(f.session.active&&f.audio.requests==1,"playing without title");check(f.session.flags==3,"media flags");check(f.audio.last.pauseOnDuck,"explicit duck callback");});
        run("10 ownership cycles and no metadata/repeated-resume stealing",()->{Fixture f=new Fixture();f.start();for(int i=0;i<10;i++){f.visible(false);check(f.session.active,"background retains controls until loss");f.audio.focus(-1);check(!f.session.active,"OEM takes control");int n=f.audio.requests;for(int j=0;j<20;j++)f.control.update(true,true);check(f.audio.requests==n&&!f.session.active,"background metadata cannot steal");f.visible(true);check(f.session.active&&f.audio.requests==n+1,"one restore");for(int j=0;j<20;j++)f.visible(true);check(f.audio.requests==n+1,"repeat resume ignored");f.key(87,0,0,100+i,1);f.key(87,0,0,100+i,1);}check(Collections.frequency(f.commands,4)==10,"one next per physical key");check(f.audio.requests==11,"11 total focus requests");check(f.audio.abandons==10,"permanent loss releases");});
        run("denied focus does not retry or forward",()->{Fixture f=new Fixture();f.audio.result=0;f.start();for(int i=0;i<100;i++)f.control.update(true,true);f.visible(true);f.control.onPlay();f.control.onSkipToNext();check(f.audio.requests==1&&!f.session.active&&f.commands.isEmpty(),"denial gate");f.visible(false);f.audio.result=1;f.visible(true);check(f.audio.requests==2&&f.session.active,"new explicit transition retries");});
        run("request exception fails closed",()->{Fixture f=new Fixture();f.audio.throwsRequest=true;f.start();f.control.update(true,true);check(!f.session.active&&f.audio.requests==1,"exception does not loop");});
        run("transient loss and navigation do not trigger re-request",()->{Fixture f=new Fixture();f.start();f.audio.focus(-2);f.visible(false);f.visible(true);f.control.update(true,false);check(!f.session.active&&f.audio.requests==1,"wait for gain");check(f.commands.equals(Arrays.asList(2)),"pause once");f.audio.focus(1);check(f.session.active&&f.audio.requests==1,"platform gain restores");check(f.commands.equals(Arrays.asList(2)),"no auto play");});
        run("duck loss suspends, repeated callbacks do not double-pause",()->{Fixture f=new Fixture();f.start();f.audio.focus(-3);f.audio.focus(-3);f.control.onSkipToNext();check(f.commands.equals(Arrays.asList(2)),"pause once, commands gated");f.audio.focus(1);check(f.session.active,"restore after duck");});
        run("permanent loss while foreground waits for a new transition",()->{Fixture f=new Fixture();f.start();f.audio.focus(-1);f.audio.focus(1);f.visible(true);f.control.update(true,true);check(!f.session.active&&f.audio.requests==1,"stale gain and update ignored");});
        run("pause does not trigger another request",()->{Fixture f=new Fixture();f.visible(true);f.visible(false);f.control.update(true,true);check(f.audio.requests==1,"no extra request after exit");f.visible(true);check(f.audio.requests==1&&f.session.active,"return restores");});
        run("background resume with retained ownership does not re-request",()->{Fixture f=new Fixture();f.start();for(int i=0;i<10;i++){f.visible(false);f.visible(true);}check(f.audio.requests==1&&f.session.active,"no needless request");});
        run("key mapping, up/repeat filtering, interleaved duplicates",()->{Fixture f=new Fixture();f.start();f.key(87,0,0,10,1);f.key(88,0,0,11,1);f.key(87,0,0,10,1);f.key(87,1,0,10,1);f.key(88,0,1,11,1);f.key(126,0,0,12,1);f.key(127,0,0,13,1);f.key(85,0,0,14,1);f.control.update(true,false);f.key(85,0,0,15,1);check(f.commands.equals(Arrays.asList(4,5,1,2,2,1)),"command mapping");});
        run("different physical presses and devices remain distinct",()->{Fixture f=new Fixture();f.start();f.key(87,0,0,10,1);f.key(87,0,0,11,1);f.key(87,0,0,11,2);check(f.commands.equals(Arrays.asList(4,4,4)),"no time debounce loses presses");});
        run("unrelated events fall through",()->{Fixture f=new Fixture();f.start();check(!f.control.onMediaButtonEvent(null),"null");Intent i=new Intent();check(!f.control.onMediaButtonEvent(i),"no key");i.action="other";check(!f.control.onMediaButtonEvent(i),"other action");check(!f.key(26,0,0,1,1),"power is not intercepted");check(f.commands.isEmpty(),"no command");});
        run("callbacks reuse original implementation and seek gate",()->{Fixture f=new Fixture();f.start();f.control.onPlay();f.control.onPause();f.control.onSkipToNext();f.control.onSkipToPrevious();f.control.onSeekTo(42);check(f.commands.equals(Arrays.asList(1,2,4,5))&&f.seeks.equals(Arrays.asList(42L)),"delegation");f.audio.focus(-1);f.control.onSeekTo(50);check(f.seeks.size()==1,"no stale seek");f.control.onStop();check(f.stops==1,"explicit stop preserved");});
        run("close is idempotent and stale callbacks cannot reactivate",()->{Fixture f=new Fixture();f.start();f.visible(false);f.control.setForeground(true);f.control.close();f.control.close();f.handler.idle();f.audio.focus(1);f.control.update(true,true);f.control.onPlay();f.control.onStop();check(!f.session.active&&f.audio.requests==1&&f.audio.abandons==1&&f.commands.isEmpty()&&f.stops==0,"closed gate");});
        run("close before first pending foreground task",()->{Fixture f=new Fixture();f.control.setForeground(true);f.control.close();f.handler.idle();f.control.update(true,true);check(f.audio.requests==0&&!f.session.active,"no late request");});
        run("foreground session stays active with empty metadata",()->{Fixture f=new Fixture();f.visible(true);f.control.update(true,false);check(f.session.active,"paused title can resume");f.control.update(false,false);check(f.session.active,"empty metadata must not undo foreground ownership");f.control.update(true,false);check(f.session.active&&f.audio.requests==1,"retained focus, no new request");});
        run("session replacement starts independent dedup state",()->{Fixture a=new Fixture();a.start();a.key(87,0,0,1,1);a.control.close();Fixture b=new Fixture();b.start();b.key(87,0,0,1,1);check(b.commands.equals(Arrays.asList(4)),"new connection key accepted");});
        run("OEM return without metadata or play restores controls immediately",()->{Fixture f=new Fixture();f.start();f.visible(false);f.audio.focus(-1);f.control.update(false,false);f.commands.clear();int before=f.audio.requests;f.visible(true);check(f.audio.requests==before+1&&f.session.active,"restore before user presses play");check(f.commands.isEmpty(),"return must not auto-play");f.key(85,0,0,999,1);check(f.commands.equals(Arrays.asList(1)),"first play key routes to CarPlay");f.control.update(false,false);check(f.session.active,"late empty metadata cannot deactivate foreground");});
        System.out.println("RESULT: "+scenarios+" scenarios; "+assertions+" assertions passed. HOST FAKES ONLY; NOT ANDROID/ART/PSA VALIDATION.");
    }
}
