"""Replace only current in the published row 9, retaining its video bitstream."""
import json,base64,urllib.request,subprocess,shutil,hashlib
from pathlib import Path
import av,imageio_ffmpeg
from material_paths import material_dir
root=Path(__file__).resolve().parents[1]
out=material_dir()/'scene-row008-trimmed-1789993088750007600'
meta=material_dir()/'scene-row008-phonetic-1789992734904632900'
patch=out/'pronunciation-current-kerrent';patch.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf8'))
old=read(meta/'request.json');word='кё́ррент'
def interval(alignment,token):
    text=''.join(alignment['characters']);assert text.count(token)==1,(token,text)
    i=text.index(token);j=i+len(token)-1
    return alignment['character_start_times_seconds'][i],alignment['character_end_times_seconds'][j]
start,end=interval(read(meta/'alignment.json')['alignment'],'ка́рэнт')
payload={'text':'Следующим шагом создадим переменную кё́ррент, которая будет играть ключевую роль в переборе массива.', 'model_id':old['model_id'],'voice_settings':old['voice_settings']}
if not (patch/'speech.mp3').exists():
    (patch/'request.json').write_text(json.dumps({'voice_id':old['voice_id'],**payload},ensure_ascii=False,indent=2),encoding='utf8')
    entries=dict(l.split('=',1) for l in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
    key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
    req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{old["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
    (patch/'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
    (patch/'alignment.json').write_text(json.dumps(reply,ensure_ascii=False),encoding='utf8')
ps,pe=interval(read(patch/'alignment.json')['alignment'],word)
duration=end-start;speed=(pe-ps)/duration
assert .5<=speed<=2,(speed,ps,pe,start,end)
source=out/'scene.mp4';target=patch/'scene.mp4'
filters=f'[0:a]atrim=end={start},asetpts=PTS-STARTPTS,afade=t=out:st={start-.003}:d=0.003[h];[1:a]atrim=start={ps}:end={pe},asetpts=PTS-STARTPTS,atempo={speed},apad,atrim=duration={duration},afade=t=in:d=0.003,afade=t=out:st={duration-.003}:d=0.003[p];[0:a]atrim=start={end},asetpts=PTS-STARTPTS,afade=t=in:d=0.003[t];[h][p][t]concat=n=3:v=0:a=1[a]'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error','-i',str(source),'-i',str(patch/'speech.mp3'),'-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(target)],check=True)
def packets(p):
    with av.open(str(p)) as c:return [bytes(packet) for packet in c.demux(video=0) if packet.size]
assert packets(source)==packets(target)
with av.open(str(target)) as c:frames=sum(1 for f in c.decode(video=0))
assert frames==790
with av.open(str(target)) as c:assert sum(f.samples for f in c.decode(audio=0))>0
backup=patch/'original-scene.mp4';assert not backup.exists()
shutil.copy2(source,backup);target.replace(source)
report={'sourceBackup':str(backup),'replacement':word,'interval':[start,end],'generatedInterval':[ps,pe],'speed':speed,'videoBitstreamUnchanged':True,'frames':frames,'publishedPathUnchanged':str(source)}
(patch/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
