"""Time semantic two-pane captures to ElevenLabs alignment, without microphone audio."""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
import av, imageio_ffmpeg, numpy as np
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();out=a.output.resolve()
scene=json.loads((out/'scene-preparation.json').read_text(encoding='utf8'))
assert hashlib.sha256(Path(scene['source']).read_bytes()).hexdigest()==scene['sha256']
assert hashlib.sha256(Path(scene['sourceFile']).read_bytes()).hexdigest()==scene['sourceSha256']
alignment=json.loads((out/'alignment.json').read_text(encoding='utf8'))['alignment'];text=''.join(alignment['characters'])
with av.open(str(out/'speech.mp3')) as c: audio_duration=c.duration/av.time_base
fps=30;frame_count=math.ceil((audio_duration+.3)*fps);duration=frame_count/fps
prefix=[]
if scene.get('transition'):
 camera=scene['transition']['camera']['samples']
 assert len(camera)>=5 and camera[0]['t']<.01 and camera[-1]['t']==1
 dy=camera[-1]['top']-camera[0]['top']
 assert all((b['top']-a['top'])*dy>=0 for a,b in zip(camera,camera[1:])),'Camera scroll reversed'
 assert max(abs(b['top']-a['top']) for a,b in zip(camera,camera[1:]))<=max(2,abs(dy)*.15),'Camera jumped'
 with av.open(scene['transition']['outputPath']) as c:
  for frame in c.decode(video=0):
   if frame.time is not None and frame.time+1e-6>=len(prefix)/fps:
    assert (frame.width,frame.height)==(1600,900)
    prefix.append(frame.to_ndarray(format='rgb24').tobytes())
 assert len(prefix)>=15,'Missing recorded scroll'
lead=len(prefix)/fps
frame_count+=len(prefix);duration=frame_count/fps
markers=[]
for cue in scene['frames']:
 assert text.count(cue['anchor'])==1, cue['anchor']
 f=Path(cue['file']);assert hashlib.sha256(f.read_bytes()).hexdigest()==cue['sha256']
 with Image.open(f) as im: assert im.size==(1600,900)
 offset=text.index(cue['anchor']);at=alignment['character_start_times_seconds'][offset]
 markers.append({**cue,'time':round(at*fps)/fps,'characterOffset':offset})
markers[0]['time']=0
assert all(b['time']>a['time'] for a,b in zip(markers,markers[1:]))
# Verify that semantic pointer actions actually changed BOTH rendered panes.
original=np.array(Image.open(markers[0]['file']).convert('RGB')).astype(int)
pointer_checks=[]
for marker in markers[1:]:
 current=np.array(Image.open(marker['file']).convert('RGB')).astype(int)
 delta=np.max(np.abs(original-current),axis=2)>30
 if marker['cellId']==markers[0]['cellId'] and marker.get('text')==markers[0].get('text') and marker['sourceStableId']==markers[0]['sourceStableId']:continue
 # Verify the configured two-zone layout; these pixels never locate pointer targets.
 if scene['placement']=='BELOW':
  split=round(900*.66);top=int(delta[:split].sum());bottom=int(delta[split:].sum())
 else:
  split=round(1600*.55);top=int(delta[:,:split].sum());bottom=int(delta[:,split:].sum())
 source_moves=marker['sourceStableId']!=markers[0]['sourceStableId']
 assert top>50 and (not source_moves or bottom>30),(marker['anchor'],top,bottom)
 pointer_checks.append({'anchor':marker['anchor'],'diagramChangedPixels':top,'sourceChangedPixels':bottom,'sourcePointerMoves':source_moves})
manifest=['ffconcat version 1.0']
for i,m in enumerate(markers):
 end=markers[i+1]['time'] if i+1<len(markers) else duration
 escaped=Path(m['file']).as_posix().replace("'","'\\''")
 manifest += [f"file '{escaped}'",f"duration {end-m['time']:.9f}"]
manifest.append(manifest[-2])
(out/'dual-frames.ffconcat').write_text('\n'.join(manifest)+'\n',encoding='utf8')
video=out/'scene-with-pointer.mp4'
# Feed every frame explicitly. Sparse concat timestamps can end the video track
# before the audio when the final still has a long hold.
images=[Image.open(m['file']).convert('RGB').tobytes() for m in markers]
encoder=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x900','-r',str(fps),'-i','pipe:0','-i',str(out/'speech.mp3'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af',f'adelay={round(lead*1000)}:all=1,apad','-t',str(duration),'-movflags','+faststart',str(video)],stdin=subprocess.PIPE)
try:
 index=0
 for pixels in prefix:encoder.stdin.write(pixels)
 for frame in range(frame_count-len(prefix)):
  while index+1<len(markers) and frame/fps>=markers[index+1]['time']:index+=1
  encoder.stdin.write(images[index])
finally:encoder.stdin.close()
assert encoder.wait()==0,'Video encoder failed'
with av.open(str(video)) as c:
 assert len(c.streams.video)==1 and len(c.streams.audio)==1
 assert (c.streams.video[0].width,c.streams.video[0].height)==(1600,900)
 decoded=sum(1 for _ in c.decode(video=0))
assert decoded==frame_count,(decoded,frame_count)
with av.open(str(video)) as c: samples=sum(f.samples for f in c.decode(audio=0))
assert samples>0
checks={'decodedVideoFrames':decoded,'expectedFrames':frame_count,'audioTrack':True,'audioSamples':samples,'twoSemanticPointers':pointer_checks,'sourceSceneUnchanged':True,'microphoneAudioUsed':False,'transitionFrames':len(prefix),'narrationStartsAt':lead}
(out/'video-check.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
(out/'markers.json').write_text(json.dumps({'text':text,'duration':duration,'narrationStartsAt':lead,'markers':[{**m,'videoTime':m['time']+lead} for m in markers],'timingSource':'ElevenLabs character alignment','coordinateSource':scene['coordinateSource']},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'video':str(video),'seconds':duration,'checks':checks},ensure_ascii=False))
