from material_paths import material_dir
"""Keep the second part of the existing take, repair only its closing sentence."""
import base64,json,subprocess,time,urllib.request
from pathlib import Path
import av,imageio_ffmpeg
root=Path(__file__).resolve().parents[1]
source=material_dir('output') / 'scene-row032-1789632865176707200'
original=json.loads((source/'request.json').read_text(encoding='utf8'))
a=json.loads((source/'alignment.json').read_text(encoding='utf8'))['alignment']
text=''.join(a['characters'])
def boundary(phrase):
    assert text.count(phrase)==1
    i=text.index(phrase)
    return (a['character_end_times_seconds'][i-1]+a['character_start_times_seconds'][i])/2
start=boundary('И конечно же')
end=boundary('Перед вами эта функция')
payload={'text':'Перед вами эта функция, которая называется он сабми́т.','model_id':original['model_id'],'voice_settings':original['voice_settings']}
out=material_dir('output')/f'row033-onsubmit-repair-{time.time_ns()}';out.mkdir()
(out/'request.json').write_text(json.dumps({'voice_id':original['voice_id'],**payload},ensure_ascii=False,indent=2),encoding='utf8')
entries=dict(line.split('=',1) for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
request=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{original["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
print('OUTPUT='+str(out),flush=True)
with urllib.request.urlopen(request,timeout=90) as response:reply=json.load(response)
(out/'patch.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
(out/'patch-alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
ff=imageio_ffmpeg.get_ffmpeg_exe()
filters=f'[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,afade=t=out:st={end-start-.005}:d=0.005[head];[1:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.005[fix];[head][fix]concat=n=2:v=0:a=1[out]'
subprocess.run([ff,'-hide_banner','-loglevel','error','-n','-i',str(source/'speech.mp3'),'-i',str(out/'patch.mp3'),'-filter_complex',filters,'-map','[out]','-c:a','pcm_s16le',str(out/'speech.wav')],check=True)
# The renderer requires a sheet snapshot; preserve the original provenance.
(out/'sheet-source.json').write_bytes((source/'sheet-source.json').read_bytes())
subprocess.run([str(root/'.venv/Scripts/python.exe'),str(root/'scripts/render_static_scene.py'),str(out),'--audio',str(out/'speech.wav'),'--background',str(source/'background.png'),'--canvas','1600x900'],check=True)
report={'source':str(source),'audio':str(out/'speech.wav'),'video':str(out/'scene-static.mp4'),'retainedInterval':[start,end],'expectedText':text[text.index('И конечно же'):].strip(),'voice':'3.3','repair':'Closing sentence only; onSubmit pronounced он сабми́т; no time stretching'}
(out/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
