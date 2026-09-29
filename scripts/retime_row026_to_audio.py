import json, math, shutil, subprocess, time
from pathlib import Path
import av, imageio_ffmpeg
from material_paths import material_dir
source=material_dir()/'scene-row026-1790237105354950100'
out=material_dir()/f'scene-row026-fast-{time.time_ns()}'
out.mkdir()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
scenario=read(source/'scenario.json')
original=Path(scenario['source'])
with av.open(str(source/'speech.mp3')) as m: audio_duration=m.duration/1e6
duration=math.ceil(audio_duration*30)/30
factor=scenario['sourceDuration']/duration
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error',
 '-i',str(original),'-i',str(source/'speech.mp3'),'-map','0:v:0','-map','1:a:0',
 '-vf',f'tpad=stop_mode=clone:stop_duration=30,setpts=(PTS-STARTPTS)/{factor},fps=30,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
 '-af','apad','-t',str(duration),'-c:v','libx264','-crf','16','-preset','slow','-pix_fmt','yuv420p',
 '-profile:v','high','-level:v','4.1','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'scene.mp4')],check=True)
with av.open(str(out/'scene.mp4')) as m:
 assert abs(sum(1 for f in m.decode(video=0))/30-duration)<.04
for n in ['sheet-source.json','request.json']:shutil.copy2(source/n,out/n)
scenario.update(duration=duration,videoSpeed=factor,audioSpeed=1,audioSource=str(source/'speech.mp3'),lastFrameHold=0)
(out/'scenario.json').write_text(json.dumps(scenario,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'output':str(out),'seconds':duration,'videoSpeed':factor}))
