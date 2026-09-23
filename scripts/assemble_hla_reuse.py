import json,math,subprocess,sys
from pathlib import Path
import av,imageio_ffmpeg
from PIL import Image,ImageDraw
out=Path(sys.argv[1]);reuse=(out/'audio-source.json').exists()
old=Path(json.loads((out/'audio-source.json').read_text())['video']) if reuse else out/'speech.mp3'
with av.open(str(old)) as m:duration=float(m.duration/av.time_base)
a=json.loads((out/'alignment.json').read_text(encoding='utf8'));a=a.get('normalized_alignment') or a['alignment']
text=''.join(a['characters']).lower()
geo=json.loads((out/'screen-geometry.json').read_text())['cells']
def cue(s):return a['character_start_times_seconds'][text.index(s)]
route=([(0,'c10'),(cue('заглушку'),'stub-check'),(cue('логикой агента'),'c8'),
        (cue('в самом начале'),'c10'),(cue('клиента'),'c14'),
        (cue('если заглушка'),'stub-check'),(cue('записываем'),'stub-record'),
        (cue('возвращаем'),'stub-yield')] if 'stub-check' in geo else
 [(0,'annotator'),(cue('структуру'),'199'),(cue('исходный код'),'source'),(cue('логи'),'logs'),(cue('агенту'),'agent'),(cue('сохраняет'),'199'),(cue('диаграмму'),'ui')] if 'annotator' in geo else
 [(0,'c8'),(cue('аннотации'),'annotation-c8'),(cue('функция querymodelwithstreaming'),'c8'),
  (cue('передаёт'),'c27'),(cue('внутри querymodel'),'c10'),
  (cue('подробнее'),'annotation-c10'),(cue('клиент anthropic'),'c14'),
  (cue('транспорт'),'c30'),(cue('http'),'c16'),
  (cue('в обратную сторону'),'c31'),(cue('события потока'),'c32'),(cue('текст ответа'),'c33')])
points=[]
for t,id in route:
 b=geo[id];points.append((t,(b['x']+b['width']*.7,b['y']+b['height']+3)))
def pos(t):
 p=points[0][1]
 for j,(end,q) in enumerate(points[1:],1):
  start=max(points[j-1][0],end-.5)
  if t<start:return p
  if t<end:
   u=(t-start)/(end-start);u=u*u*(3-2*u);return(p[0]+(q[0]-p[0])*u,p[1]+(q[1]-p[1])*u)
  p=q
 return p
(out/'scenario.json').write_text(json.dumps({'duration':duration,'voice':'3.3','audioSource':str(old),'pointerRoute':route},ensure_ascii=False,indent=2),encoding='utf8')
p=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-n','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-i',str(old),'-map','0:v','-map','1:a','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a',('copy' if reuse else 'aac'),'-movflags','+faststart',str(out/'scene.mp4')],stdin=subprocess.PIPE)
bg=Image.open(out/'scene.png').convert('RGB')
for frame in range(math.ceil(duration*30)):
 im=bg.copy();x,y=pos(frame/30)
 ImageDraw.Draw(im).polygon([(x,y),(x+5,y+40),(x+15,y+29),(x+26,y+45),(x+34,y+40),(x+23,y+24),(x+38,y+23)],fill='#ef3434',outline='white',width=2)
 p.stdin.write(im.tobytes())
p.stdin.close();assert p.wait()==0
def audio(f):
 with av.open(str(f)) as m:return [bytes(p) for p in m.demux(audio=0) if p.size]
if reuse:assert audio(old)==audio(out/'scene.mp4')
print(json.dumps({'duration':duration,'audioPacketsIdentical':True if reuse else None}))
