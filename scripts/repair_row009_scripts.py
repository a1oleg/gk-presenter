"""Replace the author clause only, preserving picture packets and later timings."""
import json, time, base64, urllib.request, subprocess, sys, hashlib
from pathlib import Path
import av, imageio_ffmpeg
from material_paths import material_dir

ROOT=Path(__file__).resolve().parents[1]
SOURCE=material_dir()/'scene-row007-1789991273237976000'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
old=read(SOURCE/'request.json')
before='Их ввёл в граф и диаграмму я, разработчик этого формата'
after='Они добавлены моими скриптами'
assert old['text'].count(before)==1
out=material_dir()/f'scene-row009-scripts-{time.time_ns()}'
out.mkdir()
save=lambda name,obj:(out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
payload={'text':after+', чтобы упростить визуализацию и двигаться к единой модели отображения любого кода в графовом виде.','model_id':old['model_id'],'voice_settings':old['voice_settings']}
save('patch-request.json',{'voice_id':old['voice_id'],**payload})
entries=dict(line.split('=',1) for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{old["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
print('OUTPUT='+str(out),flush=True)
with urllib.request.urlopen(req,timeout=120) as r:reply=json.load(r)
(out/'patch.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
save('patch-alignment.json',reply)
def interval(data,phrase):
 a=data.get('normalized_alignment') or data['alignment'];text=''.join(a['characters']);assert text.count(phrase)==1
 i=text.index(phrase);j=i+len(phrase)
 return a['character_start_times_seconds'][i],a['character_end_times_seconds'][j-1]
start,end=interval(read(SOURCE/'alignment.json'),before)
ps,pe=interval(reply,after)
span=end-start;speed=max(1,(pe-ps)/span)
assert speed<=1.15,'Patch too long: inspect before rendering'
filters=f'[0:a]atrim=end={start},asetpts=PTS-STARTPTS,afade=t=out:st={start-.005}:d=0.005[h];[1:a]atrim=start={ps}:end={pe},asetpts=PTS-STARTPTS,atempo={speed},afade=t=in:d=0.005,afade=t=out:st={max(0,(pe-ps)/speed-.005)}:d=0.005,apad,atrim=duration={span}[p];[0:a]atrim=start={end},asetpts=PTS-STARTPTS,afade=t=in:d=0.005[t];[h][p][t]concat=n=3:v=0:a=1[a]'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error','-i',str(SOURCE/'scene.mp4'),'-i',str(out/'patch.mp3'),'-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'scene.mp4')],check=True)
def fingerprint(p):
 with av.open(str(p)) as c:return hashlib.sha256(b''.join(bytes(p) for p in c.demux(video=0) if p.size)).hexdigest()
assert fingerprint(SOURCE/'scene.mp4')==fingerprint(out/'scene.mp4')
with av.open(str(out/'scene.mp4')) as c:assert sum(f.samples for f in c.decode(audio=0))>0
save('request.json',{**old,'text':old['text'].replace(before,after)})
save('repair-report.json',{'sourceVideo':str(SOURCE/'scene.mp4'),'video':str(out/'scene.mp4'),'replacedInterval':[start,end],'patchInterval':[ps,pe],'patchSpeed':speed,'pauseAdded':max(0,span-(pe-ps)/speed),'videoBitstreamUnchanged':True,'laterTimingUnchanged':True,'alignmentNote':'Original alignment applies outside replacement; patch alignment is separate.'})
print(json.dumps(read(out/'repair-report.json'),ensure_ascii=False))
