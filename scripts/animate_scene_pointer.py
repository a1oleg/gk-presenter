"""Resolve narration anchors against TTS alignment and draw a deterministic pointer.

The semantic marker plan is authored separately. This renderer neither guesses
meaning from names nor estimates timing from text length. No source edits.
"""
from pathlib import Path
import argparse,json,math,subprocess,shutil
import av
import imageio_ffmpeg
from PIL import Image,ImageDraw

parser=argparse.ArgumentParser()
parser.add_argument('output',type=Path)
parser.add_argument('--plan',type=Path,default=Path(__file__).resolve().parents[1]/'scenes/row003.markers.json')
parser.add_argument('--background',type=Path,help='Use an unchanged screenshot instead of an exported draw.io scene')
args=parser.parse_args();out=args.output
plan=json.loads(args.plan.read_text(encoding='utf-8'))
alignment=json.loads((out/'alignment.json').read_text(encoding='utf-8'))['alignment']
text=''.join(alignment['characters'])
hide_at=None
if plan.get('hideAt'):
    assert text.count(plan['hideAt'])==1
    hide_at=alignment['character_start_times_seconds'][text.index(plan['hideAt'])]
if args.background:
    with Image.open(args.background) as source_image:
        geo={'width':source_image.width,'height':source_image.height,'cells':{}}
    shutil.copyfile(args.background,out/'scene.png')
else:
    geo=json.loads((out/'screen-geometry.json').read_text())
markers=[]
for cue in plan['markers']:
    assert text.count(cue['anchor'])==1, f'Ambiguous/missing anchor: {cue["anchor"]}'
    start=text.index(cue['anchor']);end=start+len(cue['anchor'])-1
    cell=geo['cells'].get(cue.get('cellId'))
    if 'screenPosition' in cue:
        x,y=cue['screenPosition']
    elif 'routeFraction' in cue:
        points=cell['points']; lengths=[math.dist((a['x'],a['y']),(b['x'],b['y'])) for a,b in zip(points,points[1:])]
        remaining=sum(lengths)*cue['routeFraction']
        for a,b,length in zip(points,points[1:],lengths):
            if remaining<=length:
                k=remaining/length;x=a['x']+(b['x']-a['x'])*k;y=a['y']+(b['y']-a['y'])*k;break
            remaining-=length
    else:
        u,v=cue['position'];x=cell['x']+cell['width']*u;y=cell['y']+cell['height']*v
    markers.append({**cue,'time':alignment['character_start_times_seconds'][start], 'speechEnd':alignment['character_end_times_seconds'][end], 'characterRange':[start,end+1], 'x':x,'y':y})
assert all(b['time']>a['time'] for a,b in zip(markers,markers[1:]))
with av.open(str(out/'speech.mp3')) as container: duration=container.duration/av.time_base
fps=30;frames=math.ceil((duration+0.3)*fps)
for i,m in enumerate(markers):
    m['moveStart']=max(0,m['time']-plan['transitionSeconds'],markers[i-1]['time'] if i else 0)
    assert 0<=m['x']<geo['width']-50 and 0<=m['y']<geo['height']-65
resolved={'text':text,'audioDuration':duration,'videoDuration':frames/fps,'fps':fps,'markers':markers,'timingSource':'ElevenLabs character alignment','coordinatesSource':'Authored screenshot pixel targets; no resizing' if args.background else 'draw.io rendered cell geometry; screenshot fit transform applied','sourceScene':str(args.background.resolve()) if args.background else json.loads((out/'report.json').read_text(encoding='utf-8'))['scene']}
(out/'markers.json').write_text(json.dumps(resolved,ensure_ascii=False,indent=2),encoding='utf-8')
if hide_at is not None:
    resolved['pointerHiddenFrom']=hide_at
    resolved['hideReason']=plan.get('hideReason')
    (out/'markers.json').write_text(json.dumps(resolved,ensure_ascii=False,indent=2),encoding='utf-8')
background=Image.open(out/'scene.png').convert('RGB')
assert background.size==(geo['width'],geo['height'])
command=[imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{background.width}x{background.height}','-r',str(fps),'-i','pipe:0','-i',str(out/'speech.mp3'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t',str(frames/fps),'-movflags','+faststart',str(out/'scene-with-pointer.mp4')]
process=subprocess.Popen(command,stdin=subprocess.PIPE)
try:
    for frame in range(frames):
        t=frame/fps;image=background.copy()
        if t>=markers[0]['moveStart'] and (hide_at is None or t<hide_at):
            x,y=markers[0]['x'],markers[0]['y']
            for prev,nxt in zip(markers,markers[1:]):
                if t>=nxt['time']: x,y=nxt['x'],nxt['y']
                elif t>=nxt['moveStart']:
                    u=(t-nxt['moveStart'])/(nxt['time']-nxt['moveStart']);k=u*u*(3-2*u)
                    x=prev['x']+(nxt['x']-prev['x'])*k;y=prev['y']+(nxt['y']-prev['y'])*k;break
                else:break
            # Tip is the target coordinate. The shaft extends away from it.
            polygon=[(0,0),(5,38),(14,28),(29,51),(38,45),(23,23),(37,20)]
            draw=ImageDraw.Draw(image)
            points=[(round(x+dx),round(y+dy)) for dx,dy in polygon]
            draw.polygon(points,fill='#e53935')
            draw.line(points+[points[0]],fill='white',width=2,joint='curve')
        process.stdin.write(image.tobytes())
finally:
    process.stdin.close()
if process.wait()!=0: raise SystemExit('Video encoder failed')
with av.open(str(out/'scene-with-pointer.mp4')) as video:
    assert len(video.streams.video)==1 and len(video.streams.audio)==1
    assert video.streams.video[0].width==1600 and video.streams.video[0].height==900
    count=sum(1 for _ in video.decode(video=0))
    assert count==frames,(count,frames)
checks={'decodedVideoFrames':count,'expectedFrames':frames,'allTargetsInsideFrame':True,'monotonicAnchors':True,'audioTrack':True,'sourceSceneUnchanged':(out/('scene.png' if args.background else 'source.drawio')).read_bytes()==Path(resolved['sourceScene']).read_bytes()}
assert checks['sourceSceneUnchanged']
(out/'video-check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps({'output':str(out/'scene-with-pointer.mp4'),'seconds':frames/fps,'markers':[{k:m.get(k) for k in ['anchor','time','cellId','screenPosition']} for m in markers],'checks':checks},ensure_ascii=False))
