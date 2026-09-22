from material_paths import material_dir
"""Replace one clause, retaining later narration times and all video packets."""
import base64,json,subprocess,time,urllib.request,urllib.error
from pathlib import Path
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1];source=material_dir('output') / 'scene-row019-1789539624179143600'
original=json.loads((source/'request.json').read_text(encoding='utf8'))
a=json.loads((source/'alignment.json').read_text(encoding='utf8'))['alignment'];text=''.join(a['characters'])
phrase='Это значит что аннотатор может передать код функции getRandom в Модель c заданием написать аннотацию,'
assert text.count(phrase)==1 and original['text'].count(phrase)==1
fixed=phrase.replace('Модель c заданием','Модель с заданием');s=text.index(phrase);e=s+len(phrase)
previous=max(i for i in range(s) if text[i].isalnum());following=next(i for i in range(e,len(text)) if text[i].isalnum())
start=(a['character_end_times_seconds'][previous]+a['character_start_times_seconds'][s])/2
end=a['character_start_times_seconds'][following]-.04;slot=end-start
payload={'text':fixed,'previous_text':text[:s],'next_text':text[e:],'model_id':original['model_id'],'voice_settings':original['voice_settings']}
out=material_dir('output')/f'row019-cyrillic-repair-{time.time_ns()}';out.mkdir()
(out/'request.json').write_text(json.dumps({'voice_id':original['voice_id'],**payload},ensure_ascii=False,indent=2),encoding='utf8')
entries=dict(line.split('=',1) for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
request=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{original["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
print('OUTPUT='+str(out),flush=True)
try:
 with urllib.request.urlopen(request,timeout=90) as response:reply=json.load(response);cost=response.headers.get('character-cost')
except urllib.error.HTTPError as exc:raise SystemExit(f'TTS HTTP {exc.code}; no retry')
(out/'patch.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
(out/'patch-alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
b=reply['alignment'];first=next(i for i,c in enumerate(b['characters']) if c.isalnum());last=max(i for i,c in enumerate(b['characters']) if c.isalnum())
ps=max(0,b['character_start_times_seconds'][first]-.015);pe=b['character_end_times_seconds'][last]+.04
tempo=max(1,(pe-ps)/slot);assert 0<slot and tempo<1.2,'Patch too long; saved without retry'
ff=imageio_ffmpeg.get_ffmpeg_exe()
filters=f'[0:a]atrim=end={start},asetpts=PTS-STARTPTS[head];[1:a]atrim=start={ps}:end={pe},asetpts=PTS-STARTPTS,atempo={tempo},afade=t=in:d=0.005,apad,atrim=duration={slot}[fix];[0:a]atrim=start={end},asetpts=PTS-STARTPTS[tail];[head][fix][tail]concat=n=3:v=0:a=1[out]'
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(source/'speech.mp3'),'-i',str(out/'patch.mp3'),'-filter_complex',filters,'-map','[out]','-c:a','pcm_f32le',str(out/'speech.wav')],check=True)
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(out/'speech.wav'),'-c:a','libmp3lame','-b:a','128k',str(out/'speech.mp3')],check=True)
subprocess.run([str(root/'.venv/Scripts/python.exe'),str(root/'scripts/replace_scene_audio.py'),str(source/'scene-sequence.mp4'),str(out/'speech.wav'),str(out/'scene-sequence.mp4')],check=True)
report={'source':str(source),'output':str(out),'oldText':original['text'],'correctedText':original['text'].replace(phrase,fixed),'replacedInterval':[start,end],'patchText':fixed,'patchTempo':tempo,'characterCost':cost,'remainingNarrationTimingUnchanged':True}
(out/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
