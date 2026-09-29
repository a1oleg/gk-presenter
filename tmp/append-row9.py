import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio, base64, json, subprocess, time, urllib.request, sys
from pathlib import Path
import av, imageio_ffmpeg
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path('C:/GitHub/gk-presenter')
SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   async def read():
    z=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':'!A9:J9'})
    assert not z.isError
    return json.loads(z.content[0].text)
   snap=await read(); row=snap['values'][0]
   tail=row[0].strip().splitlines()[-1]
   assert tail=='А если оставшийся index больше нуля, то пойдёт на новый виток цикла.'
   assert row[8]=='3.3'
   source=material_dir('output') / 'scene-row009-headroom-20260921/scene.mp4'
   original=json.loads((material_dir('output') / 'scene-row009-1789994254508946500/request.json').read_text(encoding='utf8'))
   out=(Path(sys.argv[1]) if len(sys.argv)>1 else material_dir('output')/f'scene-row009-appended-{time.time_ns()}').resolve();out.mkdir(exist_ok=True)
   print(str(out),flush=True); save(out/'sheet-source.json',snap)
   payload={k:original[k] for k in ('model_id','voice_settings')}
   payload['text']=tail.replace('index','и́ндекс')
   save(out/'request.json',{'voice_id':original['voice_id'],**payload})
   env=dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
   key=env['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
   req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{original["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
   if not (out/'tail.mp3').exists():
    with urllib.request.urlopen(req,timeout=90) as response: reply=json.load(response)
    (out/'tail.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')));save(out/'alignment.json',reply)
   with av.open(str(out/'tail.mp3')) as media: duration=media.duration/av.time_base+.25
   # Reuse a settled frame showing the condition and both existing pointers.
   ff=imageio_ffmpeg.get_ffmpeg_exe();video=out/'scene-complete.mp4'
   filters=f'[0:v]split=2[base][still];[base]setpts=PTS-STARTPTS[v0];[still]trim=start_frame=150:end_frame=151,loop=loop=-1:size=1:start=0,setpts=N/(30*TB),trim=duration={duration},fps=30[v1];[0:a]apad,atrim=duration=17.1,asetpts=PTS-STARTPTS[a0];[1:a]apad,atrim=duration={duration},asetpts=PTS-STARTPTS[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]'
   if not video.exists():
    subprocess.run([ff,'-nostdin','-n','-hide_banner','-loglevel','error','-i',str(source),'-i',str(out/'tail.mp3'),'-filter_complex',filters,'-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(video)],check=True)
   with av.open(str(video)) as media:
    assert (media.streams.video[0].width,media.streams.video[0].height)==(1920,1080)
    frames=sum(1 for _ in media.decode(video=0));assert abs(frames/30-(17.1+duration))<.2
   with av.open(str(video)) as media: samples=sum(f.samples for f in media.decode(audio=0));assert samples>0
   report={'video':str(video),'source':str(source),'seconds':frames/30,'voice':'3.3','appendedText':tail,'originalNarrationPreserved':True,'tailVisual':'Condition frame at 5 seconds; existing diagram and code pointers','width':1920,'height':1080}
   save(out/'video-check.json',report);save(out/'scene-preparation.json',report)
   assert (await read())['values'][0]==row,'Sheet changed; output kept locally'
   z=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'Видео'!J9",'values_json':json.dumps([[str(video)]]),'value_input_option':'RAW'});assert not z.isError
   assert (await read())['values'][0]==[*row[:9],str(video)]
   print(json.dumps(report,ensure_ascii=False),flush=True)
asyncio.run(main())
