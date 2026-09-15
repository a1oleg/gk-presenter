"""Regenerate only the opening clause and keep the later narration at its original times."""
import base64,json,subprocess,time,urllib.request
from pathlib import Path
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1];source=root/'output/scene-row014-1789457488582307400'
out=root/'output'/f'row014-opening-repair-{time.time_ns()}';out.mkdir()
original=json.loads((source/'request.json').read_text(encoding='utf8'))
alignment=json.loads((source/'alignment.json').read_text(encoding='utf8'))['alignment']
text=''.join(alignment['characters']);split=text.index('покажу');cut=alignment['character_start_times_seconds'][split]
entries=dict(line.split('=',1) for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
payload={'text':'С описанием алгоритма на этом закончили,','next_text':text[split:],'model_id':original['model_id'],'voice_settings':original['voice_settings']}
request=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{original["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
print('OUTPUT='+str(out),flush=True)
with urllib.request.urlopen(request,timeout=90) as response:reply=json.load(response);cost=response.headers.get('character-cost')
(out/'opening.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
(out/'opening-alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
a=reply['alignment'];last=max(i for i,c in enumerate(a['characters']) if c.isalnum());end=a['character_end_times_seconds'][last]+.05
tempo=max(1,end/cut)
assert tempo<1.6,'Opening too long for safe fitting; generated audio saved, no retry'
ff=imageio_ffmpeg.get_ffmpeg_exe()
filters=f'[0:a]atrim=end={end},asetpts=PTS-STARTPTS,atempo={tempo},apad,atrim=duration={cut}[head];[1:a]atrim=start={cut},asetpts=PTS-STARTPTS[tail];[head][tail]concat=n=2:v=0:a=1[out]'
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(out/'opening.mp3'),'-i',str(source/'speech.mp3'),'-filter_complex',filters,'-map','[out]','-c:a','pcm_s16le',str(out/'speech.wav')],check=True)
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(out/'speech.wav'),'-c:a','libmp3lame','-b:a','128k',str(out/'speech.mp3')],check=True)
subprocess.run([str(root/'.venv/Scripts/python.exe'),str(root/'scripts/replace_scene_audio.py'),str(source/'scene-interactive.mp4'),str(out/'speech.wav'),str(out/'scene-interactive.mp4')],check=True)
report={'output':str(out),'audio':str(out/'speech.mp3'),'video':str(out/'scene-interactive.mp4'),'replacedUntilSeconds':cut,'prefixTempo':tempo,'text':payload['text'],'characterCost':cost,'restNarrationTimingUnchanged':True}
(out/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
