from material_paths import material_dir
"""Repair the missing final м, preserving the existing introduction timeline."""
import base64,json,subprocess,time,urllib.request
from pathlib import Path
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1];source=material_dir('output') / 'elevenlabs-intro-1789371724606891200';video=material_dir('output') / 'scene-row002-1789379845586042600/scene-static.mp4'
original=json.loads((source/'request.json').read_text(encoding='utf8'))
old='а потом перейдём к исходника Claude Code,';fixed='а потом перейдём к исходникам Claude Code,'
assert original['text'].count(old)==1
before,after=original['text'].split(old)
# Local Whisper word boundaries: previous word ends 7.96, next starts 10.32.
start=8.03;end=10.24;slot=end-start
payload={'text':fixed,'previous_text':before,'next_text':after,'model_id':original['model_id'],'language_code':'ru','voice_settings':original['voice_settings']}
out=material_dir('output')/f'row002-ending-repair-{time.time_ns()}';out.mkdir()
(out/'request.json').write_text(json.dumps({'voice_id':original['voice_id'],**payload},ensure_ascii=False,indent=2),encoding='utf8')
entries=dict(line.split('=',1) for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{original["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
print('OUTPUT='+str(out),flush=True)
with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response);cost=response.headers.get('character-cost')
(out/'patch.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
(out/'patch-alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
b=reply['alignment'];first=next(i for i,c in enumerate(b['characters']) if c.isalnum());last=max(i for i,c in enumerate(b['characters']) if c.isalnum())
ps=max(0,b['character_start_times_seconds'][first]-.01);pe=b['character_end_times_seconds'][last]+.03
tempo=max(1,(pe-ps)/slot);assert tempo<1.2,'Patch saved but too long; no automatic paid retry'
ff=imageio_ffmpeg.get_ffmpeg_exe()
filters=f'[0:a]atrim=end={start},asetpts=PTS-STARTPTS[head];[1:a]atrim=start={ps}:end={pe},asetpts=PTS-STARTPTS,atempo={tempo},afade=t=in:d=0.005,apad,atrim=duration={slot}[fix];[0:a]atrim=start={end},asetpts=PTS-STARTPTS[tail];[head][fix][tail]concat=n=3:v=0:a=1[out]'
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(source/'intro.wav'),'-i',str(out/'patch.mp3'),'-filter_complex',filters,'-map','[out]','-c:a','pcm_s16le',str(out/'speech.wav')],check=True)
subprocess.run([str(root/'.venv/Scripts/python.exe'),str(root/'scripts/replace_scene_audio.py'),str(video),str(out/'speech.wav'),str(out/'scene-static.mp4')],check=True)
report={'sourceAudio':str(source/'intro.wav'),'sourceVideo':str(video),'audio':str(out/'speech.wav'),'video':str(out/'scene-static.mp4'),'oldText':original['text'],'correctedText':original['text'].replace(old,fixed),'replacedInterval':[start,end],'patchTempo':tempo,'characterCost':cost,'boundarySource':'local Whisper word timing','restNarrationTimingUnchanged':True}
(out/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
