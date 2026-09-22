from material_paths import material_dir
"""One audio-only stress probe; no sheet or video changes, no paid retries."""
import base64,json,time,urllib.request
from pathlib import Path
import av

root=Path(__file__).resolve().parents[1]
source=material_dir('output') / 'scene-row015-1789459950600238400'
original=json.loads((source/'request.json').read_text(encoding='utf8'))
phrase='и размечается в графе.'
assert original['text'].count(phrase)==1
before,after=original['text'].split(phrase)
payload={
 'text':'и размечается в гра́фе.',
 'previous_text':before,
 'next_text':after,
 'model_id':original['model_id'],
 'voice_settings':original['voice_settings'],
}
out=material_dir('output')/f'row015-stress-probe-{time.time_ns()}'
out.mkdir()
(out/'request.json').write_text(json.dumps({'voice_id':original['voice_id'],**payload},ensure_ascii=False,indent=2),encoding='utf8')
entries=dict(line.split('=',1) for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
request=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{original["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
print('OUTPUT='+str(out),flush=True)
with urllib.request.urlopen(request,timeout=90) as response:
 reply=json.load(response)
 cost=response.headers.get('character-cost')
audio=out/'speech.mp3'
audio.write_bytes(base64.b64decode(reply.pop('audio_base64')))
(out/'alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
with av.open(str(audio)) as container:
 duration=container.duration/av.time_base
 assert sum(1 for _ in container.decode(audio=0))>0
report={'audio':str(audio),'seconds':duration,'text':payload['text'],'characterCost':cost,'videoAndSheetUnchanged':True}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
