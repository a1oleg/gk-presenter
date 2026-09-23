"""Retime verified UI footage to narration, independently of voice playback.

No frames are extracted to PNG. Speech is unchanged except explicit scroll pauses.
"""
import json,sys,subprocess,math
from pathlib import Path
import imageio_ffmpeg,av

old,out=map(Path,sys.argv[1:3])
load=lambda p:json.loads(p.read_text(encoding='utf8'))
record=load(old/'recording.json'); assert record['completed']
a=load(out/'alignment.json')['alignment'];text=''.join(a['characters'])
duration=math.ceil((a['character_end_times_seconds'][-1]+.8)*30)/30
old_duration=load(old/'scenario.json')['duration']
knots=[(0.,0.)]; cues=[]
for e in record['events']:
 if 'result' not in e:continue
 t=a['character_start_times_seconds'][text.index(e['phrase'])]
 # Align settled pointers with each spoken phrase, not API invocation time.
 ready=e['readyTime'];target=max(0,t-.08)
 assert ready>knots[-1][0] and target>knots[-1][1]
 knots.append((ready,target));cues.append({'phrase':e['phrase'],'speechTime':t,'pointerReadyTime':target})
knots.append((old_duration,duration))
filters=[]
for i,((s,t),(end,dest)) in enumerate(zip(knots,knots[1:])):
 filters.append(f'[0:v]trim=start={s}:end={end},setpts=(PTS-STARTPTS)*{(dest-t)/(end-s)}[v{i}]')
filters.append(''.join(f'[v{i}]' for i in range(len(knots)-1))+f'concat=n={len(knots)-1}:v=1:a=0,fps=30,tpad=stop_mode=clone:stop_duration=1[v]')
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-y','-v','error','-i',str(old/'scene.mp4'),'-i',str(out/'speech-paced.wav'),
 '-filter_complex',';'.join(filters),'-map','[v]','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',
 '-c:a','aac','-b:a','192k','-af','apad','-t',str(duration),'-movflags','+faststart',str(out/'scene.mp4')],check=True)
with av.open(str(out/'scene.mp4')) as media:
 assert (media.streams.video[0].width,media.streams.video[0].height)==(1920,1080)
 frames=sum(1 for f in media.decode(video=0));assert abs(frames/30-duration)<.1
with av.open(str(out/'scene.mp4')) as media:assert sum(f.samples for f in media.decode(audio=0))>0
(out/'scenario.json').write_text(json.dumps({'duration':duration,'voice':'3.3','cues':cues,'retimedFrom':str(old/'scene.mp4'),'timeMapping':knots},ensure_ascii=False,indent=2),encoding='utf8')
(out/'capture-validation.json').write_text(json.dumps({'frames':frames,'duration':duration,'audioSpeed':1,'addedSilenceSeconds':1.95,'horizontalCameraFixed':load(old/'capture-validation.json')['horizontalCameraFixed'],'pointerAlignment':'verified source ready times mapped to 80ms before each phrase'},indent=2),encoding='utf8')
print(str(out/'scene.mp4'))
