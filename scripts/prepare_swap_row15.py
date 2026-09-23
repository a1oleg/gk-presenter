import asyncio,base64,json,time,urllib.request,sys
from pathlib import Path
from material_paths import material_dir
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]
SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 row=int(sys.argv[1]) if len(sys.argv)>1 else 15
 out=material_dir()/f'scene-row{row:03d}-{time.time_ns()}';out.mkdir()
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   reply=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':f'!A{row}:O{row}'})
   assert not reply.isError
   snapshot=json.loads(reply.content[0].text)
 text=snapshot['values'][0][0].strip()
 if row==19:text=text.replace('проверяет своём в кэше','проверяет в своём кэше').replace('а так же','а также')
 if row==20:text=text.replace('а так же','а также')
 assert snapshot['values'][0][14]=='3.3', 'This script is configured for voice 3.3 only'
 voice=json.loads((material_dir()/'scene-row011-captions-1790056098495880100'/'request.json').read_text(encoding='utf8'))['voice_id']
 payload={'text':text,'model_id':'eleven_v3','voice_settings':{'stability':.5,'similarity_boost':1.0}}
 for name,value in [('sheet-source.json',snapshot),('request.json',{'voice_id':voice,**payload})]:
  (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
 entries=dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
 key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
 print(str(out),flush=True)
 req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=120) as response:result=json.load(response)
 (out/'speech.mp3').write_bytes(base64.b64decode(result.pop('audio_base64')))
 (out/'alignment.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf8')
 print('Generated once; no automatic paid retries.',flush=True)
asyncio.run(main())
