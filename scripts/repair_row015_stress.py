from material_paths import material_dir
"""Insert approved stress probe, preserving the timeline and video packets."""
import json,subprocess,time
from pathlib import Path
import imageio_ffmpeg

root=Path(__file__).resolve().parents[1]
source=material_dir('output') / 'scene-row015-1789459950600238400'
probe=material_dir('output') / 'row015-stress-probe-1789460213909341000'
a=json.loads((source/'alignment.json').read_text(encoding='utf8'))['alignment']
text=''.join(a['characters']);phrase='и размечается в графе.'
assert text.count(phrase)==1
s=text.index(phrase);e=s+len(phrase)
start=a['character_start_times_seconds'][s]
previous=max(i for i in range(s) if a['characters'][i].isalnum())
start=(a['character_end_times_seconds'][previous]+start)/2
following=next(i for i in range(e,len(text)) if a['characters'][i].isalnum())
end=a['character_start_times_seconds'][following]-.06
b=json.loads((probe/'alignment.json').read_text(encoding='utf8'))['alignment']
first=next(i for i,c in enumerate(b['characters']) if c.isalnum())
last=max(i for i,c in enumerate(b['characters']) if c.isalnum())
probe_start=max(0,b['character_start_times_seconds'][first]-.015)
probe_end=b['character_end_times_seconds'][last]+.035
slot=end-start;tempo=max(1,(probe_end-probe_start)/slot)
assert 0<slot and tempo<1.2, 'Approved probe does not fit without excessive acceleration'
out=material_dir('output')/f'row015-stress-repair-{time.time_ns()}';out.mkdir()
ff=imageio_ffmpeg.get_ffmpeg_exe()
filters=f'[0:a]atrim=end={start},asetpts=PTS-STARTPTS[head];[1:a]atrim=start={probe_start}:end={probe_end},asetpts=PTS-STARTPTS,atempo={tempo},afade=t=in:d=0.005,apad,atrim=duration={slot}[fix];[0:a]atrim=start={end},asetpts=PTS-STARTPTS[tail];[head][fix][tail]concat=n=3:v=0:a=1[out]'
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(source/'speech.mp3'),'-i',str(probe/'speech.mp3'),'-filter_complex',filters,'-map','[out]','-c:a','pcm_s16le',str(out/'speech.wav')],check=True)
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(out/'speech.wav'),'-c:a','libmp3lame','-b:a','128k',str(out/'speech.mp3')],check=True)
subprocess.run([str(root/'.venv/Scripts/python.exe'),str(root/'scripts/replace_scene_audio.py'),str(source/'scene-with-pointer.mp4'),str(out/'speech.wav'),str(out/'scene-with-pointer.mp4')],check=True)
report={'output':str(out),'source':str(source),'probe':str(probe),'replacedInterval':[start,end],'probeTempo':tempo,'text':'и размечается в гра́фе.','remainingNarrationTimingUnchanged':True}
(out/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
