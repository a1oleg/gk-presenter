"""Remove the repair's inserted silence from both tracks, preserving sync."""
import json, time, subprocess, shutil
from pathlib import Path
import av, imageio_ffmpeg
from material_paths import material_dir

source=material_dir()/'scene-row009-scripts-1790571026021032500'
report=json.loads((source/'repair-report.json').read_text(encoding='utf8'))
start,end=report['replacedInterval']
ps,pe=report['patchInterval']
cut_start=start+(pe-ps)/report['patchSpeed']
assert abs((end-cut_start)-report['pauseAdded'])<0.001
out=material_dir()/f'scene-row009-no-pause-{time.time_ns()}'
out.mkdir()
video=out/'scene.mp4'
filters=f'[0:v]split=2[vh][vt];[vh]trim=end={cut_start},setpts=PTS-STARTPTS[h];[vt]trim=start={end},setpts=PTS-STARTPTS[t];[0:a]asplit=2[ah][at];[ah]atrim=end={cut_start},asetpts=PTS-STARTPTS[a];[at]atrim=start={end},asetpts=PTS-STARTPTS[b];[h][a][t][b]concat=n=2:v=1:a=1[v][audio]'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error','-i',str(source/'scene.mp4'),'-filter_complex',filters,'-map','[v]','-map','[audio]','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-movflags','+faststart',str(video)],check=True)
with av.open(str(source/'scene.mp4')) as c:old_duration=c.duration/av.time_base
with av.open(str(video)) as c:
 duration=c.duration/av.time_base
 assert (c.streams.video[0].width,c.streams.video[0].height)==(1920,1080)
 frames=sum(1 for _ in c.decode(video=0))
with av.open(str(video)) as c:assert sum(f.samples for f in c.decode(audio=0))>0
assert abs(duration-(old_duration-report['pauseAdded']))<0.12
shutil.copy2(source/'request.json',out/'request.json')
result={'video':str(video),'sourceVideo':str(source/'scene.mp4'),'removedInterval':[cut_start,end],'removedSeconds':end-cut_start,'seconds':duration,'decodedFrames':frames,'bothTracksTrimmed':True,'voiceRegenerated':False}
(out/'pause-removal-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
