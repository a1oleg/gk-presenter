from material_paths import material_dir
"""Regenerate only the opening clause; retain the original narration tail."""
import base64,json,subprocess,time,urllib.request
from pathlib import Path
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1]
source=material_dir('output') / 'scene-row027-1789562286740338700'
original=json.loads((source/'request.json').read_text(encoding='utf8'))
assert original['text'].startswith('Если описать весь граф кода,')
payload={'text':'Если описать весь граф ко́да,','model_id':original['model_id'],'voice_settings':original['voice_settings']}
out=material_dir('output')/f'row027-stress-repair-{time.time_ns()}';out.mkdir()
(out/'request.json').write_text(json.dumps({'voice_id':original['voice_id'],**payload},ensure_ascii=False,indent=2),encoding='utf8')
entries=dict(line.split('=',1) for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{original["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
print('OUTPUT='+str(out),flush=True)
with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
(out/'patch.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
(out/'patch-alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
a=reply['alignment'];last=max(i for i,c in enumerate(a['characters']) if c.isalnum());end=a['character_end_times_seconds'][last]+.08
ff=imageio_ffmpeg.get_ffmpeg_exe()
filters=f'[1:a]atrim=end={end},asetpts=PTS-STARTPTS,afade=t=out:st={end-.005}:d=0.005[fix];[0:a]atrim=start=1.62,asetpts=PTS-STARTPTS,afade=t=in:d=0.005[tail];[fix][tail]concat=n=2:v=0:a=1[out]'
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(source/'speech.mp3'),'-i',str(out/'patch.mp3'),'-filter_complex',filters,'-map','[out]','-c:a','libmp3lame','-b:a','192k',str(out/'speech.mp3')],check=True)
(out/'sheet-source.json').write_bytes((source/'sheet-source.json').read_bytes())
subprocess.run([str(root/'.venv/Scripts/python.exe'),str(root/'scripts/render_static_scene.py'),str(out),'--background',str(source/'google-slide.png'),'--canvas','1600x900'],check=True)
report={'source':str(source),'audio':str(out/'speech.mp3'),'video':str(out/'scene-static.mp4'),'originalText':original['text'],'correctedText':original['text'].replace('граф кода','граф ко́да',1),'originalReplacedInterval':[0,1.62],'newOpeningDuration':end,'tailPreserved':True}
(out/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
