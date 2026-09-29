"""Compose fixed-frame draw.io reveal stages with aligned narration and pointer."""
import argparse, json, math, subprocess, hashlib
from pathlib import Path
import av, imageio_ffmpeg
from PIL import Image, ImageDraw

p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--plan',type=Path,required=True)
a=p.parse_args();out=a.output.resolve();plan=json.loads(a.plan.read_text(encoding='utf8'))
alignment=json.loads((out/'alignment.json').read_text(encoding='utf8'))['alignment']
text=''.join(alignment['characters'])
def timing(anchor):
    assert text.count(anchor)==1, f'Ambiguous or absent anchor: {anchor}'
    return alignment['character_start_times_seconds'][text.index(anchor)]
stages=[{**s,'time':s['at'] if 'at' in s else timing(s['anchor'])} for s in plan['stages']]
assert all(x['time']<y['time'] for x,y in zip(stages,stages[1:]))
images=[Image.open(out/f'stage-{i}.png').convert('RGB') for i in range(len(stages))]
geo=json.loads((out/'screen-geometry.json').read_text());size=(geo['width'],geo['height'])
assert size==(1920,1080) and all(i.size==size for i in images)
markers=[]
for m in plan['markers']:
    c=geo['cells'][m['cellId']];x=c['x']+c['width']*.85;y=c['y']+c['height']*.8
    assert 0<=x<size[0]-45 and 0<=y<size[1]-55,(m,x,y)
    t=timing(m['anchor']);index=max(i for i,s in enumerate(stages) if s['time']<=t)
    visible=json.loads((out/f'stage-{index}.json').read_text())['visible']
    assert m['cellId'] in visible, f'Pointer target hidden: {m}'
    markers.append({**m,'time':t,'x':x,'y':y})
assert all(x['time']<y['time'] for x,y in zip(markers,markers[1:]))
with av.open(str(out/'speech.mp3')) as c: duration=c.duration/1e6
frames=math.ceil((duration+.3)*30);video=out/'scene.mp4'
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{size[0]}x{size[1]}','-r','30','-i','pipe:0','-i',str(out/'speech.mp3'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t',str(frames/30),'-movflags','+faststart',str(video)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
    for f in range(frames):
        t=f/30;index=max(i for i,s in enumerate(stages) if s['time']<=t)
        im=images[index].copy()
        if index and t<stages[index]['time']+.35:
            im=Image.blend(images[index-1],im,(t-stages[index]['time'])/.35)
        x,y=markers[0]['x'],markers[0]['y']
        for prev,nxt in zip(markers,markers[1:]):
            if t>=nxt['time']:
                u=min(1,(t-nxt['time'])/.4);u=u*u*(3-2*u)
                x=prev['x']+(nxt['x']-prev['x'])*u;y=prev['y']+(nxt['y']-prev['y'])*u
            else:break
        pts=[(x+dx,y+dy) for dx,dy in [(0,0),(5,38),(14,28),(29,51),(38,45),(23,23),(37,20)]]
        d=ImageDraw.Draw(im);d.polygon(pts,fill='#e53935');d.line(pts+[pts[0]],fill='white',width=2,joint='curve')
        proc.stdin.write(im.tobytes())
finally:proc.stdin.close()
assert proc.wait()==0
with av.open(str(video)) as c: assert sum(1 for _ in c.decode(video=0))==frames
with av.open(str(video)) as c: assert sum(f.samples for f in c.decode(audio=0))>0
report={'video':str(video),'duration':frames/30,'frames':frames,'canvas':list(size),'voice':'3.3','stages':stages,'markers':markers,'framing':'fixed','sourceSha256':hashlib.sha256((out/'source.drawio').read_bytes()).hexdigest(),'timingSource':'ElevenLabs character alignment'}
(out/'scenario.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'video':str(video),'duration':frames/30,'stages':len(stages),'markers':len(markers)}))
