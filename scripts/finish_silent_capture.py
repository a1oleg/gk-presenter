import json,sys,subprocess,math
from pathlib import Path
import imageio_ffmpeg,av
out=Path(sys.argv[1]);r=json.loads((out/'recording.json').read_text());assert r['completed']
d=math.ceil(r['duration']*30)/30
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error','-i',r['recording']['outputPath'],'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-map','0:v:0','-map','1:a:0','-vf','fps=30,tpad=stop_mode=clone:stop_duration=0.2','-t',str(d),'-c:v','libx264','-crf','18','-preset','fast','-c:a','aac','-movflags','+faststart',str(out/'scene.mp4')],check=True)
with av.open(str(out/'scene.mp4')) as m:
 assert (m.streams.video[0].width,m.streams.video[0].height)==(1920,1080)
 assert abs(sum(1 for f in m.decode(video=0))/30-d)<.1
s=json.loads((out/'scenario.json').read_text());s['duration']=d;(out/'scenario.json').write_text(json.dumps(s))
print(str(out/'scene.mp4'))
