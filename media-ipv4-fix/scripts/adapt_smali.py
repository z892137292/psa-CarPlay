#!/usr/bin/env python3
"""Strict, one-shot adaptation for the SHA-256-pinned mother. No fuzzy patching."""
import pathlib
import sys

root = pathlib.Path(sys.argv[1]) / 'com/shilapi/xcertplay'

def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Expected one exact anchor: ' + old[:100])
    return text.replace(old, new)

path = root / 'AndroidPlayMediaSession.smali'
s = path.read_text()
s = replace(s, '# instance fields\n', '# instance fields\n.field private psaMedia:Lcom/shilapi/xcertplay/PsaMediaControl;\n\n')
s = replace(s,
    '    invoke-virtual {v6, v8, v9}, Landroid/media/session/MediaSession;->setCallback(Landroid/media/session/MediaSession$Callback;Landroid/os/Handler;)V',
    '''    invoke-static {v1, v6, v8, v9}, Lcom/shilapi/xcertplay/PsaMediaControl;->install(Landroid/content/Context;Landroid/media/session/MediaSession;Landroid/media/session/MediaSession$Callback;Landroid/os/Handler;)Lcom/shilapi/xcertplay/PsaMediaControl;

    move-result-object v8

    iput-object v8, v0, Lcom/shilapi/xcertplay/AndroidPlayMediaSession;->psaMedia:Lcom/shilapi/xcertplay/PsaMediaControl;''')
s = replace(s,
    '    iget-object v0, p0, Lcom/shilapi/xcertplay/AndroidPlayMediaSession;->session:Landroid/media/session/MediaSession;\n\n    invoke-virtual {p1}, Lcom/shilapi/xcertplay/media/CarPlayNowPlaying;->getTitle()Ljava/lang/String;',
    '    iget-object v0, p0, Lcom/shilapi/xcertplay/AndroidPlayMediaSession;->psaMedia:Lcom/shilapi/xcertplay/PsaMediaControl;\n\n    invoke-virtual {p1}, Lcom/shilapi/xcertplay/media/CarPlayNowPlaying;->getTitle()Ljava/lang/String;')
s = replace(s,
    '    invoke-virtual {v0, v1}, Landroid/media/session/MediaSession;->setActive(Z)V',
    '''    invoke-virtual {p1}, Lcom/shilapi/xcertplay/media/CarPlayNowPlaying;->getPlaying()Z

    move-result v4

    invoke-virtual {v0, v1, v4}, Lcom/shilapi/xcertplay/PsaMediaControl;->update(ZZ)V''')
s = replace(s, '    iput-boolean v0, p0, Lcom/shilapi/xcertplay/AndroidPlayMediaSession;->closed:Z',
    '''    iput-boolean v0, p0, Lcom/shilapi/xcertplay/AndroidPlayMediaSession;->closed:Z

    iget-object v1, p0, Lcom/shilapi/xcertplay/AndroidPlayMediaSession;->psaMedia:Lcom/shilapi/xcertplay/PsaMediaControl;

    invoke-virtual {v1}, Lcom/shilapi/xcertplay/PsaMediaControl;->close()V''')
s += '''
.method public final psaSetForeground(Z)V
    .locals 1
    iget-object v0, p0, Lcom/shilapi/xcertplay/AndroidPlayMediaSession;->psaMedia:Lcom/shilapi/xcertplay/PsaMediaControl;
    invoke-virtual {v0, p1}, Lcom/shilapi/xcertplay/PsaMediaControl;->setForeground(Z)V
    return-void
.end method
'''
path.write_text(s)

path = root / 'CarPlayHostActivity.smali'
s = path.read_text()
s = replace(s, '# instance fields\n', '# instance fields\n.field public psaMediaResumed:Z\n\n')
s = replace(s, '.method protected onPause()V\n    .locals 2', '''.method protected onPause()V
    .locals 2

    const/4 v1, 0x0
    iput-boolean v1, p0, Lcom/shilapi/xcertplay/CarPlayHostActivity;->psaMediaResumed:Z
    sget-object v0, Lcom/shilapi/xcertplay/CarPlayBackgroundSession;->INSTANCE:Lcom/shilapi/xcertplay/CarPlayBackgroundSession;
    invoke-virtual {v0, p0, v1}, Lcom/shilapi/xcertplay/CarPlayBackgroundSession;->psaSetMediaForeground(Ljava/lang/Object;Z)V''')
s = replace(s, '    invoke-super {p0}, Landroidx/activity/ComponentActivity;->onResume()V',
    '''    invoke-super {p0}, Landroidx/activity/ComponentActivity;->onResume()V

    const/4 v1, 0x1
    iput-boolean v1, p0, Lcom/shilapi/xcertplay/CarPlayHostActivity;->psaMediaResumed:Z
    sget-object v0, Lcom/shilapi/xcertplay/CarPlayBackgroundSession;->INSTANCE:Lcom/shilapi/xcertplay/CarPlayBackgroundSession;
    invoke-virtual {v0, p0, v1}, Lcom/shilapi/xcertplay/CarPlayBackgroundSession;->psaSetMediaForeground(Ljava/lang/Object;Z)V''')
path.write_text(s)

path = root / 'CarPlayBackgroundSession.smali'
s = path.read_text()
s = replace(s, '    sput-object p5, Lcom/shilapi/xcertplay/CarPlayBackgroundSession;->owner:Ljava/lang/Object;',
    '''    sput-object p5, Lcom/shilapi/xcertplay/CarPlayBackgroundSession;->owner:Ljava/lang/Object;

    instance-of v0, p5, Lcom/shilapi/xcertplay/CarPlayHostActivity;
    if-eqz v0, :psa_owner_not_host
    move-object v0, p5
    check-cast v0, Lcom/shilapi/xcertplay/CarPlayHostActivity;
    iget-boolean v1, v0, Lcom/shilapi/xcertplay/CarPlayHostActivity;->psaMediaResumed:Z
    invoke-virtual {p0, p5, v1}, Lcom/shilapi/xcertplay/CarPlayBackgroundSession;->psaSetMediaForeground(Ljava/lang/Object;Z)V
    :psa_owner_not_host''')
s += '''
.method public final declared-synchronized psaSetMediaForeground(Ljava/lang/Object;Z)V
    .locals 1
    monitor-enter p0
    :psa_try_start
    sget-object v0, Lcom/shilapi/xcertplay/CarPlayBackgroundSession;->owner:Ljava/lang/Object;
    if-ne v0, p1, :psa_done
    sget-object v0, Lcom/shilapi/xcertplay/CarPlayBackgroundSession;->systemMedia:Lcom/shilapi/xcertplay/AndroidPlayMediaSession;
    if-eqz v0, :psa_done
    invoke-virtual {v0, p2}, Lcom/shilapi/xcertplay/AndroidPlayMediaSession;->psaSetForeground(Z)V
    :psa_done
    :psa_try_end
    .catchall {:psa_try_start .. :psa_try_end} :psa_catch
    monitor-exit p0
    return-void
    :psa_catch
    move-exception v0
    monitor-exit p0
    throw v0
.end method
'''
path.write_text(s)
