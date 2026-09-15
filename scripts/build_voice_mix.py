"""Alternate original recordings at detected pauses, 60 seconds per source."""
import json,re,subprocess,time,hashlib
from pathlib import Path
import av,imageio_ffmpeg
root=Path(__file__).resolve().parents[1];out=root/'output'/f'voice-mix-{time.time_ns()}';out.mkdir()
sources=[Path('C:/Users/a1ole/Documents/Звукозаписи')/f'{n}.m4a' for n in (1,2)]
ff=imageio_ffmpeg.get_ffmpeg_exe();cuts=[]
for src in sources:
 assert src.is_file()
 result=subprocess.run([ff,'-hide_banner','-i',str(src),'-af','silencedetect=noise=-32dB:d=0.16','-f','null','-'],capture_output=True,text=True,check=True)
 starts=[float(x) for x in re.findall(r'silence_start: ([0-9.]+)',result.stderr)]
 ends=[float(x) for x in re.findall(r'silence_end: ([0-9.]+)',result.stderr)]
 pauses=[(a+b)/2 for a,b in zip(starts,ends) if b>a]
 boundaries=[0]
 for target in [20,40,59]:
  candidates=[v for v in pauses if abs(v-target)<=5 and v<60 and v>boundaries[-1]+10]
  if not candidates:raise RuntimeError(f'No safe pause near {target}s in {src.name}; inspect before cloning')
  boundaries.append(min(candidates,key=lambda x:abs(x-target)))
 cuts.append(boundaries)
filters=[];order=[];segments=[]
for block in range(3):
 for source_index in range(2):
  start,end=cuts[source_index][block:block+2];label=f's{source_index}b{block}'
  tail=f',apad=pad_dur={60-end}' if block==2 else ''
  filters.append(f'[{source_index}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,aresample=24000,aformat=sample_fmts=s16:channel_layouts=mono{tail}[{label}]')
  order.append(f'[{label}]');segments.append({'source':str(sources[source_index]),'start':start,'end':end,'silencePadding':60-end if block==2 else 0})
filters.append(''.join(order)+'concat=n=6:v=0:a=1[out]')
sample=out/'voice1-voice2-120s.wav'
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(sources[0]),'-i',str(sources[1]),'-filter_complex',';'.join(filters),'-map','[out]','-c:a','pcm_s16le',str(sample)],check=True)
with av.open(str(sample)) as c:
 duration=c.duration/1e6;assert abs(duration-120)<.01
report={'sample':str(sample),'duration':duration,'secondsPerSource':60,'segments':segments,'sourceHashes':{str(s):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},'processing':'Pause-aligned concatenation; mono 24kHz; no denoise, pitch shift or speed change'}
(out/'mix-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
