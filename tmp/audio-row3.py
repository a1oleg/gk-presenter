import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio,base64,json,time,urllib.request
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/gk-presenter'); SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':'!A1:J3'});assert not result.isError
   snap=json.loads(result.content[0].text);row=snap['values'][2]
   assert row[1:9]==['VS Code OBS','services/api/claude.ts:1051:5:1051:27','services/api/claude.ts:1063:10:1066:5','75','1','нет','нет','3.3']
   text=row[0].replace('функции с которой','функции, с которой').replace('пользователь подключившийся','пользователь, подключившийся').replace('проверяется не','проверяется, не').replace('модель .','модель.').replace(' \n','\n').strip()
   out=material_dir('output')/f'scene-row003-{time.time_ns()}';out.mkdir()
   (out/'sheet-source.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding='utf8')
   voice=json.loads((material_dir('output') / 'voice-mix-comparison-1789454509647/voice.local.json').read_text())['voice_id']
   env=dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'));key=env['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
   payload={'text':text,'model_id':'eleven_v3','voice_settings':{'stability':0.5,'similarity_boost':1.0}}
   (out/'request.json').write_text(json.dumps({'voice_id':voice,**payload},ensure_ascii=False,indent=2),encoding='utf8')
   print('OUTPUT='+str(out),flush=True)
   req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
   with urllib.request.urlopen(req,timeout=90) as response:reply=json.load(response)
   (out/'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
   (out/'alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
   print('AUDIO_READY',flush=True)
asyncio.run(main())
