"""Remove the final sentence at its aligned boundary; no speech generation."""
import json,subprocess,time
from pathlib import Path
import av,imageio_ffmpeg
root=Path(__file__).resolve().parents[1]
source=root/'output/scene-row008-background-1789453393461204500'
out=root/'output'/f'scene-row008-trimmed-{time.time_ns()}';out.mkdir()
alignment=json.loads((source/'alignment.json').read_text(encoding='utf8'))
a=alignment['alignment'];text=''.join(a['characters']);index=text.index('В упрощённом виде')
cut=a['character_start_times_seconds'][index]-.04
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-n','-i',str(source/'speech.mp3'),'-t',str(cut),'-c:a','libmp3lame','-b:a','128k',str(out/'speech.mp3')],check=True)
subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-n','-i',str(source/'scene-with-pointer.mp4'),'-t',str(cut),'-c:v','libx264','-crf','18','-preset','fast','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'scene-with-pointer.mp4')],check=True)
for key,data in alignment.items():
 if isinstance(data,dict) and 'character_start_times_seconds' in data:
  n=sum(t<cut for t in data['character_start_times_seconds'])
  for field in ['characters','character_start_times_seconds','character_end_times_seconds']:
   data[field]=data[field][:n]
(out/'alignment.json').write_text(json.dumps(alignment,ensure_ascii=False,indent=2),encoding='utf8')
with av.open(str(out/'scene-with-pointer.mp4')) as c:
 assert len(c.streams.audio)==1
 frames=sum(1 for _ in c.decode(video=0));assert abs(frames/30-cut)<.05
report={'output':str(out),'audio':str(out/'speech.mp3'),'video':str(out/'scene-with-pointer.mp4'),'cutSeconds':cut,'frames':frames,'removedText':text[index:],'sourceVideo':str(source/'scene-with-pointer.mp4')}
(out/'trim-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
