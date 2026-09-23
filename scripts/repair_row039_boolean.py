"""Replace one pronunciation sentence, preserving video and all other audio timing."""
import base64,json,subprocess,time,urllib.request,shutil,sys
from pathlib import Path
import av,imageio_ffmpeg
from material_paths import material_dir

root=Path(__file__).resolve().parents[1]
source=material_dir()/'scene-row039-1790162578182894400'
request=json.loads((source/'request.json').read_text(encoding='utf8'))
a=json.loads((source/'alignment.json').read_text(encoding='utf8'))['alignment'];text=''.join(a['characters'])
def boundary(phrase):
 assert text.count(phrase)==1
 i=text.index(phrase)
 return (a['character_end_times_seconds'][i-1]+a['character_start_times_seconds'][i])/2
start,end=boundary('На диаграмме'),boundary('Диагональная штриховка')
out=Path(sys.argv[1]) if len(sys.argv)>1 else material_dir()/f'scene-row039-boolean-{time.time_ns()}'
out.mkdir(exist_ok=True)
payload={'text':'На диаграмме это гекс, то есть бу́левае значение.','model_id':request['model_id'],'voice_settings':request['voice_settings']}
entries=dict(l.split('=',1) for l in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
(out/'patch-request.json').write_text(json.dumps({'voice_id':request['voice_id'],**payload},ensure_ascii=False,indent=2),encoding='utf8')
print('OUTPUT='+str(out),flush=True)
req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{request["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
if not (out/'patch.mp3').exists():
 with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
 (out/'patch.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
 (out/'patch-alignment.json').write_text(json.dumps(reply,ensure_ascii=False),encoding='utf8')
with av.open(str(out/'patch.mp3')) as media:
 patch_duration=sum(f.samples/f.sample_rate for f in media.decode(audio=0))
span=end-start;speed=max(1,patch_duration/span)
assert speed<1.5,'Replacement too long; keep generated sample without publishing'
ff=imageio_ffmpeg.get_ffmpeg_exe()
filters=f'[0:a]atrim=end={start},asetpts=PTS-STARTPTS,afade=t=out:st={start-.005}:d=0.005[h];[1:a]asetpts=PTS-STARTPTS,atempo={speed},apad,atrim=duration={span},afade=t=in:d=0.005,afade=t=out:st={span-.005}:d=0.005[p];[0:a]atrim=start={end},asetpts=PTS-STARTPTS,afade=t=in:d=0.005[t];[h][p][t]concat=n=3:v=0:a=1[a]'
subprocess.run([ff,'-nostdin','-n','-v','error','-i',str(source/'scene.mp4'),'-i',str(out/'patch.mp3'),'-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'scene.mp4')],check=True)
for name in ['request.json','sheet-source.json','scenario.json']:shutil.copy2(source/name,out/name)
# Stream copy must preserve the complete encoded picture stream byte-for-byte.
def video_packets(file):
 with av.open(str(file)) as m:return [bytes(p) for p in m.demux(video=0) if p.size]
assert video_packets(source/'scene.mp4')==video_packets(out/'scene.mp4')
(out/'repair-report.json').write_text(json.dumps({'source':str(source),'replacementInterval':[start,end],'patchPlaybackSpeed':speed,'videoBitstreamUnchanged':True,'sheetTextUnchanged':True},indent=2),encoding='utf8')
print(str(out/'scene.mp4'))
