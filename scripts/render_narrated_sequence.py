"""Compose real draw.io exports with speech-aligned view changes and pointers."""
import argparse,json,math,subprocess,hashlib
from pathlib import Path
import av,imageio_ffmpeg
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--plan',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
plan=json.loads(a.plan.read_text(encoding='utf8'));alignment=json.loads((out/'alignment.json').read_text(encoding='utf8'))['alignment'];text=''.join(alignment['characters'])
def time_for(anchor):
 assert text.count(anchor)==1,anchor
 return alignment['character_start_times_seconds'][text.index(anchor)]
views=[{**v,'time':v.get('at',0) if 'at' in v else time_for(v['anchor'])} for v in plan['views']]
assert all(a['time']<b['time'] for a,b in zip(views,views[1:]))
images={v['name']:Image.open(out/v['name']/'scene.png').convert('RGB') for v in views}
assert all(img.size==(1600,900) for img in images.values())
geos={name:json.loads((out/name/'screen-geometry.json').read_text()) for name in images}
markers=[]
for m in plan['markers']:
 c=geos[m['view']]['cells'][m['cellId']];u,v=m['position'];x=c['x']+c['width']*u;y=c['y']+c['height']*v
 assert 0<=x<1550 and 0<=y<835,(m,x,y)
 markers.append({**m,'time':time_for(m['anchor']),'x':x,'y':y})
with av.open(str(out/'speech.mp3')) as c:duration=c.duration/1e6
frames=math.ceil((duration+.3)*30);video=out/'scene-sequence.mp4'
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x900','-r','30','-i','pipe:0','-i',str(out/'speech.mp3'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t',str(frames/30),'-movflags','+faststart',str(video)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
 for frame in range(frames):
  t=frame/30;view=next(v for v in reversed(views) if v['time']<=t);image=images[view['name']].copy()
  visible=[m for m in markers if m['view']==view['name']]
  if visible:
   x,y=visible[0]['x'],visible[0]['y']
   for previous,nxt in zip(visible,visible[1:]):
    start=max(previous['time'],nxt['time']-plan['transitionSeconds'])
    if t>=nxt['time']:x,y=nxt['x'],nxt['y']
    elif t>=start:
     u=(t-start)/(nxt['time']-start);k=u*u*(3-2*u);x=previous['x']+(nxt['x']-previous['x'])*k;y=previous['y']+(nxt['y']-previous['y'])*k;break
    else:break
   polygon=[(x+dx,y+dy) for dx,dy in [(0,0),(5,38),(14,28),(29,51),(38,45),(23,23),(37,20)]]
   draw=ImageDraw.Draw(image);draw.polygon(polygon,fill='#e53935');draw.line(polygon+[polygon[0]],fill='white',width=2,joint='curve')
  proc.stdin.write(image.tobytes())
finally:proc.stdin.close()
assert proc.wait()==0
with av.open(str(video)) as c:
 assert len(c.streams.audio)==1 and len(c.streams.video)==1
 assert sum(1 for _ in c.decode(video=0))==frames
with av.open(str(video)) as c:assert sum(f.samples for f in c.decode(audio=0))>0
for source in json.loads((out/'scene-sources.json').read_text()):assert hashlib.sha256(Path(source['file']).read_bytes()).hexdigest()==source['sha256']
report={'video':str(video),'audio':str(out/'speech.mp3'),'duration':frames/30,'frames':frames,'views':views,'markers':markers,'sourceDiagramsUnchanged':True,'annotationSource':'authored-scene-snippet','timingSource':'ElevenLabs character alignment'}
(out/'sequence-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
