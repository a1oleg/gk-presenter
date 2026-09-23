import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio,base64,json,subprocess,time,urllib.request,sys
from pathlib import Path
import av,imageio_ffmpeg
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/graphKoda-presenter');SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   async def read(n):
    z=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':n});assert not z.isError;return json.loads(z.content[0].text)
   if len(sys.argv)>1:
    out=Path(sys.argv[1]).resolve();snap=json.loads((out/'sheet-source.json').read_text(encoding='utf8'));scenario=json.loads((out/'scenario-source.json').read_text(encoding='utf8'))
   else:
    snap=await read('!A11:K11');scenario=await read("'ФЙ-сценарий'!A1:N4")
    out=material_dir('output')/f'scene-row011-captions-{time.time_ns()}';out.mkdir();save(out/'sheet-source.json',snap);save(out/'scenario-source.json',scenario)
   print('OUTPUT='+str(out),flush=True)
   rows=scenario['values'];text=rows[3][0];assert snap['values'][0][9]=='3.3'
   if not (out/'speech.mp3').exists():
    voice=json.loads((material_dir('output') / 'scene-row009-1789994254508946500/request.json').read_text(encoding='utf8'))['voice_id']
    payload={'text':text,'model_id':'eleven_v3','voice_settings':{'stability':.5,'similarity_boost':1.0}};save(out/'request.json',{'voice_id':voice,**payload})
    env=dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
    req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':env['ELEVENLABS_API_KEY'].strip().strip('"').strip("'"),'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
    (out/'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')));save(out/'alignment.json',reply)
   subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'tmp/render-row11-captions.py'),str(out)],check=True)
   save(out/'captions.json',{'sourceRange':"'ФЙ-сценарий'!B2:N4",'position':[0,990],'size':[1920,90],'states':rows[1:4]})
   if not (out/'scene-preparation.json').exists():return
   with av.open(str(out/'speech.mp3')) as a:duration=a.duration/av.time_base+.35
   prep=json.loads((out/'scene-preparation.json').read_text(encoding='utf8'));video=out/'scene.mp4'
   if not video.exists():
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-i',prep['recording'],'-i',str(out/'speech.mp3'),'-i',str(out/'captions.png'),'-filter_complex','[0:v]fps=30,setsar=1[v];[v][2:v]overlay=0:990[out]','-map','[out]','-map','1:a','-af','apad','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(video)],check=True)
   with av.open(str(video)) as m:
    assert (m.streams.video[0].width,m.streams.video[0].height)==(1920,1080);frames=sum(1 for _ in m.decode(video=0));assert abs(frames/30-duration)<.2
   with av.open(str(video)) as m:assert sum(f.samples for f in m.decode(audio=0))>0
   save(out/'video-check.json',{'video':str(video),'seconds':frames/30,'voice':'3.3','captionRange':"'ФЙ-сценарий'!A1:N4",'sceneFramingPreserved':True})
   assert (await read('!A11:K11'))['values']==snap['values'];assert (await read("'ФЙ-сценарий'!A1:N4"))['values']==scenario['values']
   z=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'Видео'!K11",'values_json':json.dumps([[str(video)]]),'value_input_option':'RAW'});assert not z.isError
   assert (await read('!K11'))['values']==[[str(video)]];print('K11 VERIFIED '+str(video))
asyncio.run(main())
