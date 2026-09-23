"""Append only new sheet narration over the final frame of a finished clip."""
import json,sys,subprocess,time,base64,urllib.request,asyncio,math
from pathlib import Path
from material_paths import material_dir
root=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')

def render(out,source):
 import av,imageio_ffmpeg
 original=read(source/'scenario.json')['duration']
 a=read(out/'append-alignment.json')['alignment']
 duration=math.ceil((original+a['character_end_times_seconds'][-1]+.6)*30)/30
 subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error','-i',str(source/'scene.mp4'),'-i',str(out/'append.mp3'),
  '-filter_complex',f'[0:v]tpad=stop_mode=clone:stop_duration={duration-original},fps=30[v];[0:a]apad,atrim=duration={original},asetpts=PTS-STARTPTS[a0];[1:a]asetpts=PTS-STARTPTS[a1];[a0][a1]concat=n=2:v=0:a=1,apad[a]',
  '-map','[v]','-map','[a]','-t',str(duration),'-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'scene.mp4')],check=True)
 with av.open(str(out/'scene.mp4')) as m:
  assert (m.streams.video[0].width,m.streams.video[0].height)==(1920,1080)
  assert abs(sum(1 for f in m.decode(video=0))/30-duration)<.1
 scenario=read(source/'scenario.json');scenario.update(duration=duration,appendStart=original,sourceVideo=str(source/'scene.mp4'),tailScene='last frame held')
 save(out/'scenario.json',scenario)
 print(str(out/'scene.mp4'))

async def prepare(source,row):
 from mcp import ClientSession,StdioServerParameters
 from mcp.client.stdio import stdio_client
 previous=read(source/'sheet-source.json');original=previous['values'][0][0].strip()
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':previous['spreadsheetId'],'notation':f'!A{row}:P{row}'})
   assert not result.isError;snapshot=json.loads(result.content[0].text)
 full=snapshot['values'][0][0].strip();assert full.startswith(original),'Earlier text changed; not a pure append'
 tail=full[len(original):].strip();assert tail,'Nothing appended'
 old=read(source/'request.json');payload={k:old[k] for k in ['model_id','voice_settings']};payload['text']=tail
 out=material_dir()/f'scene-row{row:03d}-append-{time.time_ns()}';out.mkdir()
 save(out/'sheet-source.json',snapshot);save(out/'append-request.json',{'voice_id':old['voice_id'],**payload});save(out/'request.json',{**old,'text':full,'segments':[{'source':str(source/'scene.mp4')},{'request':'append-request.json'}]})
 entries=dict(l.split('=',1) for l in (root/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
 key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
 req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{old["voice_id"]}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
 print('OUTPUT='+str(out),flush=True)
 with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
 (out/'append.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')));save(out/'append-alignment.json',reply)
 subprocess.run([str(root/'.venv/Scripts/python.exe'),__file__,'--render',str(out),str(source)],check=True)

if sys.argv[1]=='--render':render(Path(sys.argv[2]),Path(sys.argv[3]))
else:asyncio.run(prepare(Path(sys.argv[1]),int(sys.argv[2])))
