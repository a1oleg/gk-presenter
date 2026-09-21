import asyncio,base64,json,subprocess,time,urllib.request
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/coldKode-presenter');SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':SID,'notation':'!A1:J7'}
   snap=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);row=snap['values'][6]
   assert row[1:9]==['VS Code OBS','examples/fisher-yates/src/shuffle.ts:6:7:33:1:flow-start','нет','110','2','нет','справа','3.3']
   text=row[0].strip().replace('означает что','означает, что').replace('переменной - тут','переменной — тут').replace('cоздадим','создадим')
   spoken=text.replace('Claude Code','Клод Код')
   out=ROOT/'output'/f'scene-row007-{time.time_ns()}';out.mkdir();print('OUTPUT='+str(out),flush=True)
   (out/'sheet-source.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding='utf8')
   env=dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'));key=env['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
   voice=json.loads((ROOT/'output/voice-mix-comparison-1789454509647/voice.local.json').read_text())['voice_id']
   payload={'text':spoken,'model_id':'eleven_v3','voice_settings':{'stability':0.5,'similarity_boost':1.0}}
   (out/'pronunciation.json').write_text(json.dumps({'displayText':text,'replacements':{'Claude Code':'Клод Код'}},ensure_ascii=False,indent=2),encoding='utf8')
   (out/'request.json').write_text(json.dumps({'voice_id':voice,**payload},ensure_ascii=False,indent=2),encoding='utf8')
   req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
   with urllib.request.urlopen(req,timeout=90) as res:reply=json.load(res)
   (out/'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')));(out/'alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
   subprocess.run(['node',str(ROOT/'tmp/record-row7.mjs'),str(out)],check=True,cwd=ROOT)
   subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'tmp/mux-row3.py'),str(out)],check=True,cwd=ROOT)
   fresh=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert fresh['values'][6]==row,'Sheet changed; video saved locally'
   video=str(out/'scene.mp4');updated=[text,*row[1:9],video]
   result=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'Видео'!A7:J7",'values_json':json.dumps([updated]),'value_input_option':'RAW'});assert not result.isError
   verify=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert verify['values'][6]==updated
   print(json.dumps({'video':video,'sheetVerified':True}),flush=True)
asyncio.run(main())
