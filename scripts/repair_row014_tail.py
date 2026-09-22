"""Recover the recorded false transition; reuse narration without resynthesis."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import av
import imageio_ffmpeg
from material_paths import material_dir

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
args = p.parse_args()
out = args.directory.resolve()
assert out.is_relative_to(material_dir())
recording = json.loads((out/'recording.json').read_text(encoding='utf-8'))
original = out/'scene-interactive.mp4'
raw = Path(recording['outputPath'])
audio = out/'speech.mp3'
video = out/'scene-interactive-v2.mp4'
false = next(e for e in recording['events'] if e['input'].get('id') == 'segment-2')
# Keep the repeat click and remove only the idle verification gap before false.
cut = 27.6
resume = round(false['time']*30)/30
with av.open(str(raw)) as c:
    raw_seconds = c.duration/1e6
duration = cut+raw_seconds-resume+2
assert resume > cut and raw_seconds-resume > false['input']['durationMs']/1000+0.5
digest = lambda file: hashlib.sha256(file.read_bytes()).hexdigest()
before = {str(file):digest(file) for file in [original,raw,audio]}
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-n',
    '-i',str(original),'-i',str(raw),'-i',str(audio),
    '-filter_complex',f'[0:v]trim=end={cut},setpts=PTS-STARTPTS[a];[1:v]trim=start={resume},setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0,fps=30,tpad=stop_mode=clone:stop_duration=2[v]',
    '-map','[v]','-map','2:a','-c:v','libx264','-crf','16','-preset','medium',
    '-c:a','aac','-b:a','192k','-af','apad','-t',str(duration),'-movflags','+faststart',str(video)],check=True)
assert before == {file:digest(Path(file)) for file in before}
frames=0
with av.open(str(video)) as c:
    assert (c.streams.video[0].width,c.streams.video[0].height)==(1920,1080)
    for frame in c.decode(video=0): frames+=1
assert abs(frames/30-duration)<0.15
with av.open(str(video)) as c: audio_frames=sum(1 for _ in c.decode(audio=0))
assert audio_frames>0
report={'video':str(video),'original':str(original),'preservedThrough':cut,'rawResumedAt':resume,
        'falseMovementCompleteBy':cut+false['input']['durationMs']/1000,
        'seconds':frames/30,'frames':frames,'audioFrames':audio_frames,'sourceHashes':before,
        'narrationReused':True,'finalHoldAdded':2}
(out/'tail-repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
