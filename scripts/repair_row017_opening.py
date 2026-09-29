"""Replace opening pronunciation only; keep video packets and all later timing."""
import json, time, base64, urllib.request, subprocess, shutil, sys
from pathlib import Path
import av, imageio_ffmpeg
from material_paths import material_dir
root=Path(__file__).resolve().parents[1]
source=material_dir()/'scene-row017-1790233102211202300'
out=Path(sys.argv[1]) if len(sys.argv)>1 else material_dir()/f'scene-row017-opening-{time.time_ns()}'
out.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf8'))
old=read(source/'request.json')
alignment=read(source/'alignment.json')['alignment']
text=''.join(alignment['characters'])
assert text.startswith('Claude Code это')
end=alignment['character_start_times_seconds'][text.index('это')]
payload={'text':'Клод код это React-подобное приложение на TypeScript.',
         'model_id':old['model_id'],'voice_settings':old['voice_settings']}
(out/'patch-request.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf8')
print('OUTPUT='+str(out),flush=True)
if not (out/'patch.mp3').exists():
 entries=dict(l.split('=',1) for l in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
 key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
 req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{old["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
 (out/'patch.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
 (out/'patch-alignment.json').write_text(json.dumps(reply,ensure_ascii=False),encoding='utf8')
a=read(out/'patch-alignment.json')['alignment'];t=''.join(a['characters'])
assert t.startswith('Клод код это')
pend=a['character_start_times_seconds'][t.index('это')]
speed=pend/end
assert .5<=speed<=2, (speed,pend,end)
filters=f'[1:a]atrim=end={pend},asetpts=PTS-STARTPTS,atempo={speed},apad,atrim=duration={end},afade=t=out:st={end-.003}:d=0.003[p];[0:a]atrim=start={end},asetpts=PTS-STARTPTS,afade=t=in:d=0.003[t];[p][t]concat=n=2:v=0:a=1[a]'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error','-i',str(source/'scene.mp4'),'-i',str(out/'patch.mp3'),'-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'scene.mp4')],check=True)
for n in ['sheet-source.json','scenario.json']:shutil.copy2(source/n,out/n)
old['text']=old['text'].replace('Claude Code','Клод код',1)
(out/'request.json').write_text(json.dumps(old,ensure_ascii=False),encoding='utf8')
def packets(p):
 with av.open(str(p)) as c:return [bytes(p) for p in c.demux(video=0) if p.size]
assert packets(source/'scene.mp4')==packets(out/'scene.mp4')
(out/'repair-report.json').write_text(json.dumps({'source':str(source),'replacedInterval':[0,end],'patchSpeed':speed,'videoBitstreamUnchanged':True}),encoding='utf8')
print(str(out/'scene.mp4'))
