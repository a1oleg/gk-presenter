import sys,json,subprocess,math
from pathlib import Path
import av,imageio_ffmpeg
out=Path(sys.argv[1]).resolve();scene=json.loads((out/'scene-preparation.json').read_text(encoding='utf8'))
with av.open(str(out/'speech.mp3')) as c:duration=c.duration/av.time_base+.3
video=out/'scene.mp4'
with av.open(scene['recording']) as c: width,height=c.streams.video[0].width,c.streams.video[0].height
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-i',scene['recording'],'-i',str(out/'speech.mp3'),'-map','0:v:0','-map','1:a:0','-vf','fps=30,setsar=1','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t',str(duration),'-movflags','+faststart',str(video)],check=True)
with av.open(str(video)) as c:
 assert (c.streams.video[0].width,c.streams.video[0].height)==(width,height)
 frames=sum(1 for f in c.decode(video=0));assert abs(frames/30-duration)<.1
with av.open(str(video)) as c:samples=sum(f.samples for f in c.decode(audio=0));assert samples>0
report={'video':str(video),'seconds':frames/30,'frames':frames,'audioSamples':samples,'width':width,'height':height,'voice':'3.3','microphoneAudioUsed':False}
(out/'video-check.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
