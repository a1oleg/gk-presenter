"""Add a speech-aligned pointer without changing the existing audio stream."""
import json, shutil, subprocess, sys, time, unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
import av
import imageio_ffmpeg
from PIL import ImageDraw

source=Path(sys.argv[1]); out=source.parent/f'scene-row017-pointer-{time.time_ns()}';out.mkdir()
for name in ['sheet-source.json','request.json','alignment.json','scenario.json','source.drawio','waiting.drawio','validate_geometry.json']:
    shutil.copy2(source/name,out/name)
scenario=json.loads((out/'scenario.json').read_text(encoding='utf8'))
alignment=json.loads((out/'alignment.json').read_text(encoding='utf8'))
a=alignment.get('normalized_alignment') or alignment['alignment']
chars=[];indices=[]
for i,c in enumerate(a['characters']):
    for ch in unicodedata.normalize('NFD',c.lower()):
        if unicodedata.category(ch)!='Mn':chars.append(ch);indices.append(i)
text=''.join(chars)
def cue(word):
    i=text.index(word);return a['character_start_times_seconds'][indices[i]]
root=ET.parse(out/'waiting.drawio').getroot()
camera=scenario['camera'];scale=camera['scale']
def world(x,y):return ((x-camera['x'])*scale,(y-camera['y'])*scale)
def target(id):
    node=root.find(f'.//mxCell[@id="{id}"]/mxGeometry')
    x,y,w,h=(float(node.get(k)) for k in ['x','y','width','height'])
    return world(x+w*.7,y+h+4)
route=[(0,target('c8')),(cue('shuffle'),target('c8')),
       (cue('гетрэндом'),target('c10')),(cue('своп'),target('c14')),
       (cue('в таком случае')+.2,target('presenter-wait')),
       (cue('спускается'),world(286,938)),
       (cue('по связям'),world(706,938)),
       (cue('графа'),world(286,1138.645669)),
       (cue('к вызываемым'),target('c14'))]
scenario['pointer']={'route':[{'time':t,'x':p[0],'y':p[1]} for t,p in route],'transitionSeconds':.45,'size':42,'color':'#ef3434'}
(out/'scenario.json').write_text(json.dumps(scenario,ensure_ascii=False,indent=2),encoding='utf8')
def position(t):
    p=route[0][1]
    for j in range(1,len(route)):
        when,q=route[j]
        start=max(route[j-1][0],when-.45)
        if t<start:return p
        if t<when:
            u=(t-start)/(when-start);u=u*u*(3-2*u)
            return (p[0]+(q[0]-p[0])*u,p[1]+(q[1]-p[1])*u)
        p=q
    return p
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-n',
     '-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0',
     '-i',str(source/'scene.mp4'),'-map','0:v','-map','1:a','-c:v','libx264',
     '-crf','18','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(out/'scene.mp4')]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
with av.open(str(source/'scene.mp4')) as video:
    for frame in video.decode(video=0):
        img=frame.to_image();x,y=position(float(frame.time))
        points=[(x,y),(x+5,y+40),(x+15,y+29),(x+26,y+45),(x+34,y+40),(x+23,y+24),(x+38,y+23)]
        ImageDraw.Draw(img).polygon(points,fill='#ef3434',outline='white',width=2)
        proc.stdin.write(img.tobytes())
proc.stdin.close();assert proc.wait()==0
def audio_packets(file):
    with av.open(str(file)) as media:
        return [bytes(p) for p in media.demux(audio=0) if p.size]
assert audio_packets(source/'scene.mp4')==audio_packets(out/'scene.mp4'),'Audio changed'
print(str(out))
