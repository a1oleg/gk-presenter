"""Replace the last sentence, retaining its natural duration and original scene."""
import json,base64,urllib.request,subprocess,shutil,sys
from pathlib import Path
import av,imageio_ffmpeg
from material_paths import material_dir
root=Path(__file__).resolve().parents[1]
out=material_dir()/'scene-row031-1790241445371125300'
patch=out/'ending-repair';patch.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf8'))
old=read(out/'request.json');a=read(out/'alignment.json')['alignment']
text=''.join(a['characters']);i=text.index('Классно')
start=a['character_start_times_seconds'][i]
payload={'text':'Классно, что он так умеет. Но это, конечно, не повод расслабля́ться.',
 'model_id':old['model_id'],'voice_settings':old['voice_settings']}
(patch/'request.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
if not (patch/'speech.mp3').exists():
 entries=dict(l.split('=',1) for l in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
 key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
 req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{old["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
 (patch/'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
 (patch/'alignment.json').write_text(json.dumps(reply,ensure_ascii=False),encoding='utf8')
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
filters=f'[0:a]atrim=end={start},asetpts=PTS-STARTPTS,afade=t=out:st={start-.003}:d=0.003[h];[1:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.003[t];[h][t]concat=n=2:v=0:a=1[a]'
subprocess.run([ffmpeg,'-nostdin','-n','-v','error','-i',str(out/'speech.mp3'),'-i',str(patch/'speech.mp3'),'-filter_complex',filters,'-map','[a]','-c:a','pcm_s16le',str(patch/'full-speech.wav')],check=True)
shutil.copy2(out/'sheet-source.json',patch/'sheet-source.json')
subprocess.run([sys.executable,str(root/'scripts/render_static_scene.py'),str(patch),'--audio',str(patch/'full-speech.wav'),'--background',str(out/'background.png'),'--canvas','1920x1080','--no-upscale','--background-color','0x292929'],check=True)
report=read(patch/'static-video-report.json')
backup=patch/'original-scene.mp4';assert not backup.exists()
shutil.copy2(out/'scene.mp4',backup)
(patch/'scene-static.mp4').replace(out/'scene.mp4')
scenario=read(out/'scenario.json');scenario.update(duration=report['seconds'],audio='ending-repair/full-speech.wav',audioRepair='ending-repair/repair-report.json')
(out/'scenario.json').write_text(json.dumps(scenario,ensure_ascii=False,indent=2),encoding='utf8')
repair={'replacedFrom':start,'replacementText':payload['text'],'speechSpeed':1,'duration':report['seconds'],'originalSpeechPreservedUntil':start,'sourceBackup':str(backup),'sceneUnchanged':True}
(patch/'repair-report.json').write_text(json.dumps(repair,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(repair,ensure_ascii=False))
