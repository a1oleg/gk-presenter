"""Replace only the mispronounced/incorrect word, keeping the picture stream."""
import json,sys,time,subprocess,base64,urllib.request,shutil
from pathlib import Path
import av,imageio_ffmpeg
from material_paths import material_dir
root=Path(__file__).resolve().parents[1]
source=material_dir()/'scene-row042-1790166932836277000'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
old=read(source/'request.json');a=read(source/'alignment.json')['alignment']
def interval(a,word):
 text=''.join(a['characters']);assert text.count(word)==1
 i=text.index(word);j=i+len(word)
 return a['character_start_times_seconds'][i],a['character_end_times_seconds'][j-1]
start,end=interval(a,'показа')
out=Path(sys.argv[1]) if len(sys.argv)>1 else material_dir()/f'scene-row042-word-{time.time_ns()}'
out.mkdir(exist_ok=True)
payload={'text':'Этот выбор пока́зан в виде горизонтальной развилки.','model_id':old['model_id'],'voice_settings':old['voice_settings']}
(out/'patch-request.json').write_text(json.dumps({'voice_id':old['voice_id'],**payload},ensure_ascii=False),encoding='utf8')
print('OUTPUT='+str(out),flush=True)
if not (out/'patch.mp3').exists():
 entries=dict(l.split('=',1) for l in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
 key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
 req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{old["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
 (out/'patch.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
 (out/'patch-alignment.json').write_text(json.dumps(reply,ensure_ascii=False),encoding='utf8')
p=read(out/'patch-alignment.json')['alignment'];pstart,pend=interval(p,'пока́зан')
span=end-start;speed=(pend-pstart)/span;assert .5<=speed<=2
filters=f'[0:a]atrim=end={start},asetpts=PTS-STARTPTS,afade=t=out:st={start-.003}:d=0.003[h];[1:a]atrim=start={pstart}:end={pend},asetpts=PTS-STARTPTS,atempo={speed},apad,atrim=duration={span},afade=t=in:d=0.003,afade=t=out:st={span-.003}:d=0.003[p];[0:a]atrim=start={end},asetpts=PTS-STARTPTS,afade=t=in:d=0.003[t];[h][p][t]concat=n=3:v=0:a=1[a]'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error','-i',str(source/'scene.mp4'),'-i',str(out/'patch.mp3'),'-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'scene.mp4')],check=True)
for n in ['sheet-source.json','scenario.json']:shutil.copy2(source/n,out/n)
old['text']=old['text'].replace('выбор показа в','выбор показан в')
(out/'request.json').write_text(json.dumps(old,ensure_ascii=False),encoding='utf8')
def packets(f):
 with av.open(str(f)) as m:return [bytes(p) for p in m.demux(video=0) if p.size]
assert packets(source/'scene.mp4')==packets(out/'scene.mp4')
(out/'repair-report.json').write_text(json.dumps({'source':str(source),'word':'показан','replacedInterval':[start,end],'patchInterval':[pstart,pend],'patchSpeed':speed,'videoBitstreamUnchanged':True},indent=2),encoding='utf8')
print(str(out/'scene.mp4'))
