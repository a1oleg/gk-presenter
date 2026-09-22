import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio,base64,json,subprocess,time,urllib.request
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/coldKode-presenter'); SHEETS=ROOT.parent/'google-sheets-mcp'
SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 async with stdio_client(StdioServerParameters(command=str(SHEETS/'.venv/Scripts/python.exe'),args=[str(SHEETS/'server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   async def read():
    v=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':'!A1:I3'})
    assert not v.isError
    return json.loads(v.content[0].text)
   snap=await read(); row=snap['values'][1]
   assert snap['values'][0][:9]==['текст','сцена','стартовый узел','масштаб VS code','указка','интерактив','код','голос','ссылка на видео']
   assert row[1:8]==['VS Code OBS\nGoogle Slides OBS','services/api/claude.ts:1051:5:1051:27','75','нет','нет','нет','3.3']
   out=material_dir('output')/f'scene-row002-{time.time_ns()}';out.mkdir()
   (out/'sheet-source.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding='utf8')
   subprocess.run(['node',str(ROOT/'tmp/capture-row2.mjs'),str(out)],check=True)
   env=dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
   key=env['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
   voice=json.loads((material_dir('output') / 'voice-mix-comparison-1789454509647/voice.local.json').read_text())['voice_id']
   payload={'text':row[0].strip(),'model_id':'eleven_v3','voice_settings':{'stability':0.5,'similarity_boost':1.0}}
   (out/'request.json').write_text(json.dumps({'voice_id':voice,**payload},ensure_ascii=False,indent=2),encoding='utf8')
   print('OUTPUT='+str(out),flush=True)
   req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
   with urllib.request.urlopen(req,timeout=90) as response: reply=json.load(response)
   (out/'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
   (out/'alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
   subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'scripts/render_static_scene.py'),str(out),'--background',str(out/'scene.png'),'--canvas','1600x900'],check=True)
   fresh=await read(); assert fresh['values']==snap['values'],'Sheet changed; video saved without publication'
   video=str(out/'scene-static.mp4')
   result=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'"+snap['sheetTitle'].replace("'","''")+"'!I2",'values_json':json.dumps([[video]]),'value_input_option':'RAW'})
   assert not result.isError
   verified=await read();assert verified['values'][1][:8]==row[:8] and verified['values'][1][8]==video
   print(json.dumps({'video':video,'sheetVerified':True},ensure_ascii=False))
asyncio.run(main())
