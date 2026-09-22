from material_paths import material_dir
"""Replace only final phrase, retaining the original video and narration prefix."""
import base64,json,subprocess,time,urllib.request
from pathlib import Path
import av,imageio_ffmpeg
root=Path(__file__).resolve().parents[1];source=material_dir('output') / 'scene-row028-1789625221129126900'
original=json.loads((source/'request.json').read_text(encoding='utf8'))
a=json.loads((source/'alignment.json').read_text(encoding='utf8'))['alignment'];text=''.join(a['characters'])
phrase='в графе зависимостей';fixed='в гра́фе зависимостей'
i=text.index(phrase);previous=a['character_end_times_seconds'][i-1];start=(previous+a['character_start_times_seconds'][i])/2
payload={'text':'Улучшить ранжирование кандидатов за счёт их близости в гра́фе зависимостей.','model_id':original['model_id'],'voice_settings':original['voice_settings']}
out=material_dir('output')/f'row028-stress-repair-{time.time_ns()}';out.mkdir()
(out/'request.json').write_text(json.dumps({'voice_id':original['voice_id'],**payload},ensure_ascii=False,indent=2),encoding='utf8')
entries=dict(line.split('=',1) for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
request=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{original["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
print('OUTPUT='+str(out),flush=True)
with urllib.request.urlopen(request,timeout=90) as response:reply=json.load(response)
(out/'patch.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
(out/'patch-alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
b=reply['alignment'];bt=''.join(b['characters']);bi=bt.index('в гра');ps=max(0,b['character_start_times_seconds'][bi]-.01)
last=max(i for i,c in enumerate(b['characters']) if c.isalnum());pe=b['character_end_times_seconds'][last]+.05
with av.open(str(source/'speech.mp3')) as c:duration=c.duration/1e6
slot=duration-start;tempo=max(1,(pe-ps)/slot);assert tempo<1.25,'Patch saved but too long; no automatic retry'
ff=imageio_ffmpeg.get_ffmpeg_exe()
filters=f'[0:a]atrim=end={start},asetpts=PTS-STARTPTS,afade=t=out:st={start-.005}:d=0.005[head];[1:a]atrim=start={ps}:end={pe},asetpts=PTS-STARTPTS,atempo={tempo},afade=t=in:d=0.005,apad,atrim=duration={slot}[fix];[head][fix]concat=n=2:v=0:a=1[out]'
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(source/'speech.mp3'),'-i',str(out/'patch.mp3'),'-filter_complex',filters,'-map','[out]','-c:a','pcm_s16le',str(out/'speech.wav')],check=True)
subprocess.run([str(root/'.venv/Scripts/python.exe'),str(root/'scripts/replace_scene_audio.py'),str(source/'scene-with-pointer.mp4'),str(out/'speech.wav'),str(out/'scene-with-pointer.mp4')],check=True)
report={'source':str(source),'audio':str(out/'speech.wav'),'video':str(out/'scene-with-pointer.mp4'),'originalText':original['text'],'correctedText':original['text'].replace(phrase,fixed),'replacedInterval':[start,duration],'patchInterval':[ps,pe],'tempo':tempo,'prefixPreserved':True}
(out/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
