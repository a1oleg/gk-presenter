"""Mux semantic capture with narration, excluding all live microphone audio."""
import json, subprocess, sys, math
from pathlib import Path
import av, imageio_ffmpeg
out=Path(sys.argv[1]).resolve()
record=json.loads((out/'recording.json').read_text(encoding='utf8'))
assert record['completed']
duration=math.ceil(record['duration']*30)/30
audio=out/'speech-paced.wav' if (out/'speech-paced.wav').exists() else out/'speech.mp3'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-y','-hide_banner','-loglevel','error',
 '-i',record['recording']['outputPath'],'-i',str(audio),'-map','0:v:0','-map','1:a:0',
 '-vf','fps=30,tpad=stop_mode=clone:stop_duration=0.5','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',
 '-c:a','aac','-b:a','192k','-af','apad','-t',str(duration),'-movflags','+faststart',str(out/'scene.mp4')],check=True)
with av.open(str(out/'scene.mp4')) as media:
 assert (media.streams.video[0].width,media.streams.video[0].height)==(1920,1080)
 frames=0
 for frame in media.decode(video=0):
  if frames%30==0:
   pixels=frame.reformat(width=64,height=36,format='gray').to_ndarray()
   assert pixels.var()>20,'Blank capture'
  frames+=1
 assert abs(frames/30-duration)<.1
with av.open(str(out/'scene.mp4')) as media:assert sum(f.samples for f in media.decode(audio=0))>0
assert all(e['result']['frame']['visible'] for e in record['events'] if 'result' in e)
initial=json.loads((out/'initial-scene.json').read_text(encoding='utf8')) if (out/'initial-scene.json').exists() else {}
code_fixed=None
for event in record['events']:
 camera=event.get('camera')
 if camera:
  assert all(abs(s['left']-initial['initialCamera']['camera']['scrollLeft'])<1 for s in camera['transition']['samples']),'Horizontal motion during vertical scroll'
if initial.get('codeRangeFits'):
 start=initial['opened']['visibleRanges'][0]['startLine']
 code_fixed=all(e['result']['code']['visibleStartLine']==start for e in record['events'] if 'result' in e)
 assert code_fixed,'Fully visible source range was scrolled'
chunk_events=[e for e in record['events'] if e.get('type')=='chunk-scroll']
if chunk_events:
 # The first chunk must not move while its visible nodes are narrated.
 first_scroll=chunk_events[0]['time']
 early=[e for e in record['events'] if 'result' in e and e['actualTime']<first_scroll]
 assert len(early)>=2
 assert all(e['result']['frame']['camera']==initial['initialCamera']['camera'] for e in early),'Initial chunk moved during narration'
 for e in record['events']:
  if e.get('type')=='generator-reveal':
   a,b=e['before'],e['after']
   assert abs(a['screenBounds']['y']-b['screenBounds']['y']-e['minimalScroll'])<3,'Generator scrolled farther than needed'
(out/'capture-validation.json').write_text(json.dumps({'frames':frames,'duration':duration,'semanticTargetsVisible':True,'horizontalCameraFixed':True,'codeStayedAtInitialRange':code_fixed,'microphoneAudioUsed':False},indent=2),encoding='utf8')
scenario=json.loads((out/'scenario.json').read_text(encoding='utf8'));scenario['duration']=duration
(out/'scenario.json').write_text(json.dumps(scenario,ensure_ascii=False,indent=2),encoding='utf8')
print(str(out/'scene.mp4'))
