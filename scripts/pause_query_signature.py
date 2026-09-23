"""Insert silence at aligned phrase boundaries; preserve the recorded voice."""
import json, sys, subprocess, wave
from pathlib import Path
import imageio_ffmpeg

out=Path(sys.argv[1]).resolve()
assert not (out/'narration-pacing.json').exists(),'Prepare a fresh retake; do not apply pauses twice'
data=json.loads((out/'alignment.json').read_text(encoding='utf8'))
a=data['alignment']; text=''.join(a['characters'])
plan=[('доступные инструменты',.95),('После параметров',1.0)]
rate=48000
pcm=subprocess.check_output([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(out/'speech.mp3'),'-f','s16le','-ac','1','-ar',str(rate),'-'])
pauses=[]
for phrase,seconds in plan:
 i=text.index(phrase); j=i-1
 while j>=0 and (text[j].isspace() or text[j] in ',.—:'):j-=1
 prev=a['character_end_times_seconds'][j]
 start=a['character_start_times_seconds'][i]
 assert start>=prev,(phrase,prev,start)
 pauses.append({'phrase':phrase,'at':(prev+start)/2,'seconds':seconds,'index':i})
cursor=0; chunks=[]; shift=0
for p in pauses:
 point=round(p['at']*rate)*2
 chunks.extend([pcm[cursor:point],bytes(round(p['seconds']*rate)*2)])
 p['pauseStart']=p['at']+shift;shift+=p['seconds'];cursor=point
chunks.append(pcm[cursor:])
with wave.open(str(out/'speech-paced.wav'),'wb') as w:
 w.setparams((1,2,rate,0,'NONE','not compressed'));w.writeframes(b''.join(chunks))
for key in ('alignment','normalized_alignment'):
 if key not in data or data[key] is None:continue
 for field in ('character_start_times_seconds','character_end_times_seconds'):
  data[key][field]=[t+sum(p['seconds'] for p in pauses if p['at']<=t) for t in data[key][field]]
(out/'alignment-original.json').write_text((out/'alignment.json').read_text(encoding='utf8'),encoding='utf8')
(out/'alignment.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf8')
(out/'narration-pacing.json').write_text(json.dumps({'audioFile':'speech-paced.wav','addedSeconds':shift,'pauses':pauses},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'addedSeconds':shift,'pauses':pauses},ensure_ascii=False))
