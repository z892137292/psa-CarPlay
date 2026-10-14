package com.shilapi.xcertplay;

import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.AudioFocusRequest;
import android.media.AudioManager;
import android.media.session.MediaSession;
import android.os.Handler;
import android.util.Log;
import android.view.KeyEvent;
import java.util.ArrayDeque;

/** API 28 adapter around the mother APK's original callback. No transport changes. */
public final class PsaMediaControl extends MediaSession.Callback
        implements AudioManager.OnAudioFocusChangeListener {
    private static final String TAG = "PSA-MEDIA";
    private final AudioManager audio;
    private final MediaSession session;
    private final MediaSession.Callback original;
    private final Handler handler;
    private final AudioFocusRequest request;
    private final ArrayDeque<String> recentPresses = new ArrayDeque<String>();
    private boolean closed;
    private boolean foreground;
    private boolean pending;
    private boolean requested;
    private boolean suspended = true;
    private boolean eligible;
    private boolean playing;

    private PsaMediaControl(Context context, MediaSession session,
            MediaSession.Callback original, Handler handler) {
        this.audio = (AudioManager) context.getSystemService(Context.AUDIO_SERVICE);
        this.session = session;
        this.original = original;
        this.handler = handler;
        this.request = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
                .setAudioAttributes(new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
                .setWillPauseWhenDucked(true)
                .setOnAudioFocusChangeListener(this, handler).build();
    }

    public static PsaMediaControl install(Context context, MediaSession session,
            MediaSession.Callback original, Handler handler) {
        PsaMediaControl control = new PsaMediaControl(context, session, original, handler);
        session.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS
                | MediaSession.FLAG_HANDLES_TRANSPORT_CONTROLS);
        session.setCallback(control, handler);
        // No new receiver: the live session receives events directly. Never cold-start playback.
        session.setMediaButtonReceiver(null);
        return control;
    }

    public void setForeground(final boolean visible) {
        handler.post(new Runnable() {
            @Override public void run() { foregroundChanged(visible); }
        });
    }

    private synchronized void foregroundChanged(boolean visible) {
        if (closed || foreground == visible) return;
        foreground = visible;
        // Cancel an unconsumed attempt on exit; preserve existing background playback ownership.
        pending = visible && !requested;
        Log.i(TAG, "foreground=" + visible + " requested=" + requested);
        restoreOnce();
    }

    /** Called on the original publisher's main handler after its revision check. */
    public synchronized void update(boolean hasTitle, boolean isPlaying) {
        if (closed) return;
        playing = isPlaying;
        eligible = hasTitle || isPlaying;
        restoreOnce();
        refreshActive();
    }

    private void restoreOnce() {
        if (closed || !pending || !foreground || !eligible || requested) return;
        pending = false; // Consume before the platform call: no retry on metadata or key events.
        int result = AudioManager.AUDIOFOCUS_REQUEST_FAILED;
        if (audio != null) {
            try { result = audio.requestAudioFocus(request); }
            catch (RuntimeException e) { Log.w(TAG, "focus request failed: " + e.getClass().getSimpleName()); }
        }
        requested = result == AudioManager.AUDIOFOCUS_REQUEST_GRANTED;
        suspended = !requested;
        refreshActive();
        Log.i(TAG, "restore result=" + result + " active=" + session.isActive());
    }

    @Override public synchronized void onAudioFocusChange(int change) {
        if (closed || !requested) return; // Ignore stale gain after release or denial.
        Log.i(TAG, "focus=" + change + " foreground=" + foreground);
        if (change == AudioManager.AUDIOFOCUS_LOSS
                || change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT
                || change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK) {
            boolean wasControlling = !suspended;
            suspended = true;
            pending = false;
            session.setActive(false);
            if (change == AudioManager.AUDIOFOCUS_LOSS) {
                requested = false;
                abandon();
            }
            // Existing phone command pauses music once. Navigation/transport code is untouched.
            if (wasControlling && playing) {
                Log.i(TAG, "focus-loss pause via existing controller");
                original.onPause();
            }
        } else if (change == AudioManager.AUDIOFOCUS_GAIN) {
            suspended = false;
            refreshActive();
            // Do not auto-play the phone after calls/navigation; the user retains playback choice.
        }
    }

    private void refreshActive() {
        boolean active = !closed && requested && !suspended && eligible;
        if (session.isActive() != active) session.setActive(active);
    }

    private boolean canDispatch() {
        return !closed && requested && !suspended && session.isActive();
    }

    private void dispatch(int code) {
        if (!canDispatch()) {
            Log.i(TAG, "drop code=" + code + " suspended=" + suspended);
            return;
        }
        Log.i(TAG, "dispatch code=" + code + " phoneAck=unknown");
        switch (code) {
            case 1: original.onPlay(); break;
            case 2: original.onPause(); break;
            case 4: original.onSkipToNext(); break;
            case 5: original.onSkipToPrevious(); break;
            default: break;
        }
    }

    @Override public synchronized boolean onMediaButtonEvent(Intent intent) {
        if (intent == null || !Intent.ACTION_MEDIA_BUTTON.equals(intent.getAction())) return false;
        KeyEvent event = intent.getParcelableExtra(Intent.EXTRA_KEY_EVENT);
        if (event == null) return false;
        int key = event.getKeyCode();
        if (key != 85 && key != 87 && key != 88 && key != 126 && key != 127) return false;
        Log.i(TAG, "key=" + key + " action=" + event.getAction() + " repeat=" + event.getRepeatCount());
        if (event.getAction() != KeyEvent.ACTION_DOWN || event.getRepeatCount() != 0) return true;
        String press = key + ":" + event.getDownTime() + ":" + event.getDeviceId();
        if (recentPresses.contains(press)) return true;
        // Keep a small history so interleaved duplicate deliveries are also suppressed.
        if (recentPresses.size() == 32) recentPresses.removeFirst();
        recentPresses.addLast(press);
        int command = key == 87 ? 4 : key == 88 ? 5 : key == 126 ? 1 : key == 127 ? 2 : playing ? 2 : 1;
        dispatch(command);
        return true; // Never also call super: that would dispatch the same physical press again.
    }

    @Override public synchronized void onPlay() { dispatch(1); }
    @Override public synchronized void onPause() { dispatch(2); }
    @Override public synchronized void onSkipToNext() { dispatch(4); }
    @Override public synchronized void onSkipToPrevious() { dispatch(5); }
    @Override public synchronized void onSeekTo(long position) {
        if (canDispatch()) original.onSeekTo(position);
    }
    @Override public synchronized void onStop() {
        if (!closed) original.onStop(); // Preserve the mother's explicit disconnect action.
    }

    private void abandon() {
        if (audio != null) {
            try { audio.abandonAudioFocusRequest(request); }
            catch (RuntimeException e) { Log.w(TAG, "focus abandon failed: " + e.getClass().getSimpleName()); }
        }
    }

    public synchronized void close() {
        if (closed) return;
        closed = true;
        pending = false;
        boolean release = requested;
        requested = false;
        suspended = true;
        recentPresses.clear();
        session.setActive(false);
        if (release) abandon();
    }
}
