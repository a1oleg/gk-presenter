"""Sequence -> flow -> annotated sequence, with cuts and narration pointers."""
import json, subprocess, sys, unicodedata, math
from pathlib import Path
import av, imageio_ffmpeg
from PIL import Image, ImageDraw
out=Path(sys.argv[1])
data=json.loads((out/'alignment.json').read_text(encoding='utf8'))
a=data.get('normalized_alignment') or data['alignment']
chars=[];positions=[]
for i,ch in enumerate(a['characters']):
    for c in unicodedata.normalize('NFD',ch.lower()):
        if unicodedata.category(c)!='Mn':chars.append(c);positions.append(i)
text=''.join(chars)
def cue(s):
    s=''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
    return a['character_start_times_seconds'][positions[text.index(s)]]
is19='A19:' in json.loads((out/'sheet-source.json').read_text(encoding='utf8'))['range']
is20='A20:' in json.loads((out/'sheet-source.json').read_text(encoding='utf8'))['range']
single=is19 or is20
stepAt=cue('декомпозируется') if is20 else None
cut1,cut2=(float('inf'),cue('получилось движение')) if is20 else ((float('inf'),cue('можно описывать')) if is19 else (cue('вспоминаем'),cue('обходчик')))
with av.open(str(out/'speech.mp3')) as m:duration=sum(f.samples/f.sample_rate for f in m.decode(audio=0))
camera={'x':110,'y':598,'scale':1080/940,'width':1200,'height':940}
def xy(x,y):return ((x-110)*camera['scale'],(y-598)*camera['scale'])
# World coordinates refer to the actual sequence heads and getRandom flow mosaic.
route=([(0,xy(300,660)),(cue('готовые контексты'),xy(800,850)),
       (cue('нижних веток'),xy(960,1210)),(cue('если функция большая'),xy(300,660)),
       (stepAt+.1,xy(345,775)),(cue('отдельным шагам'),xy(345,865)),
       (cut2,xy(375,700)),(cue('сначала спуск'),xy(706,938)),
       (cue('недостающими смыслами'),xy(874,1138)),(cue('затем подъем'),xy(375,700)),
       (cue('сходить наверх'),xy(300,660)),(cue('собирается контекст'),xy(680,700))] if is20 else
      [(0,xy(885,1160)),(cue('готового описания'),xy(930,1150)),
       (cue('если его нет'),xy(885,1160)),(cut2,xy(950,1195))] if is19 else
      [(0,xy(735,809)),(cut1,xy(735,809)),
       (cue('математические'),xy(870,924)),
       (cue('системной границей'),xy(947,924)),
       (cue('этот код'),xy(870,924)),
       (cut2,xy(779,791)),
       (cue('получает описание'),xy(805,835)),
       (cue('сохраняет'),xy(1140,835))])
def pointer(t):
    p=route[0][1]
    for j in range(1,len(route)):
        end,q=route[j];start=max(route[j-1][0],end-.5)
        if t<start:return p
        if t<end:
            u=(t-start)/(end-start);u=u*u*(3-2*u)
            return(p[0]+(q[0]-p[0])*u,p[1]+(q[1]-p[1])*u)
        p=q
    return p
images=[Image.open(out/(n+'.png')).convert('RGB') for n in (['before','before','waiting'] if single else ['before','flow','waiting'])]
if is20:images.append(Image.open(out/'steps.png').convert('RGB'))
scenario={'duration':duration,'camera':camera,'voice':'3.3','events':[
    *([] if single else [{'time':cut1,'action':'cut','scene':'flow'}]),
    *([{'time':stepAt,'action':'show','cells':['presenter-step-1','presenter-step-2']}] if is20 else []),
    {'time':cut2,'action':'cut','scene':'sequence-with-annotation'}],
    'pointer':{'route':[{'time':t,'x':p[0],'y':p[1]} for t,p in route]}}
(out/'scenario.json').write_text(json.dumps(scenario,ensure_ascii=False,indent=2),encoding='utf8')
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-n','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-i',str(out/'speech.mp3'),'-map','0:v','-map','1:a','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'scene.mp4')]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for frame in range(math.ceil(duration*30)):
    t=frame/30
    index=(0 if t<stepAt else 3 if t<cut2 else 2) if is20 else ((0 if t<cut2 else 2) if single else (0 if t<cut1 else 1 if t<cut2 else 2))
    image=images[index].copy();x,y=pointer(t)
    ImageDraw.Draw(image).polygon([(x,y),(x+5,y+40),(x+15,y+29),(x+26,y+45),(x+34,y+40),(x+23,y+24),(x+38,y+23)],fill='#ef3434',outline='white',width=2)
    p.stdin.write(image.tobytes())
p.stdin.close();assert p.wait()==0
print(json.dumps({'duration':duration,'flowAt':cut1,'annotationAt':cut2}))
