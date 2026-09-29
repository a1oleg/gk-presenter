"""Generate the edited prefix only, retain the unchanged original final paragraph."""
import json,sys,subprocess,time,base64,urllib.request,hashlib
from pathlib import Path
from material_paths import material_dir
root=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf8'))
anchor='Граф с аннотациями становится системой'
source=material_dir()/'scene-row027-1789562286740338700'
if len(sys.argv)>1 and sys.argv[1]=='--render':
 import imageio_ffmpeg
 out=Path(sys.argv[2]);a=read(source/'alignment.json')['alignment'];t=''.join(a['characters'])
 start=a['character_start_times_seconds'][t.index(anchor)]
 # Take the untouched tail from the original synthesis, before any opening repair.
 filters=f'[0:a]asetpts=PTS-STARTPTS[p];[1:a]atrim=start={start},asetpts=PTS-STARTPTS,afade=t=in:d=0.003[t];[p][t]concat=n=2:v=0:a=1[a]'
 subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error','-i',str(out/'prefix.mp3'),'-i',str(source/'speech.mp3'),'-filter_complex',filters,'-map','[a]','-c:a','pcm_s16le',str(out/'speech.wav')],check=True)
 report={'sourceTail':str(source/'speech.mp3'),'sourceTailStart':start,'tailText':read(out/'request.json')['text'].split(anchor,1)[1],'tailRegenerated':False,'speed':1}
 (out/'audio-reuse.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 sys.exit()
raw=subprocess.check_output(['C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',str(root/'tmp/read_row2.py'),'!A33:O33'],encoding='utf8')
snapshot=json.loads(raw);row=snapshot['values'][0];text=row[0].strip()
old=read(source/'request.json');assert text.count(anchor)==1
assert text.split(anchor,1)[1]==old['text'].split(anchor,1)[1],'Final paragraph changed'
out=material_dir()/f'scene-row033-prefix-{time.time_ns()}';out.mkdir()
(out/'sheet-source.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf8')
request={**old,'text':text}
(out/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf8')
payload={'text':text.split(anchor,1)[0].strip(),'model_id':old['model_id'],'voice_settings':old['voice_settings']}
(out/'prefix-request.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
entries=dict(l.split('=',1) for l in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{old["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
print('OUTPUT='+str(out),flush=True)
with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
(out/'prefix.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
(out/'prefix-alignment.json').write_text(json.dumps(reply,ensure_ascii=False),encoding='utf8')
subprocess.run([str(root/'.venv/Scripts/python.exe'),__file__,'--render',str(out)],check=True)
print(str(out))
