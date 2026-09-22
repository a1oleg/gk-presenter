import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio,base64,json,subprocess,time,urllib.request,sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/coldKode-presenter');SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
ROW=int(sys.argv[1]) if len(sys.argv)>1 else 7
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':SID,'notation':f'!A1:J{ROW}'}
   snap=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);row=snap['values'][ROW-1]
   assert row[1:4]==['VS Code OBS','examples/fisher-yates/src/shuffle.ts:6:7:33:1:flow-start','examples/fisher-yates/src/shuffle.ts:26:1:30:3:for' if ROW==9 else 'нет'] and row[5:9]==['2','нет','справа','3.3']
   text=row[0].strip().replace('означает что','означает, что').replace('переменной - тут','переменной — тут').replace('cоздадим','создадим').replace('метод который','метод, который').replace('функций которых','функций, которых').replace('не тоже самое что','не то же самое, что').replace(' \n','\n')
   spoken=text.replace('Claude Code','Клод Код')
   text=text.replace('Очевидно что','Очевидно, что').replace('из-за того что','из-за того, что').replace('length это','length — это').replace('подстветки','подсветки')
   if ROW==9:
    text=text.replace('гексами у которых','гексами, у которых').replace('узел в котором','узел, в котором').replace('проверяться не достигнут','проверяться, не достигнут')
   replacements={'Claude Code':'Клод Код',**({'for':'фор','true':'тру','false':'фолс'} if ROW==9 else {})}
   spoken=text
   for term,pronunciation in replacements.items():spoken=spoken.replace(term,pronunciation)
   out=material_dir('output')/f'scene-row{ROW:03d}-{time.time_ns()}';out.mkdir();print('OUTPUT='+str(out),flush=True)
   (out/'sheet-source.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding='utf8')
   env=dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'));key=env['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
   voice=json.loads((material_dir('output') / 'voice-mix-comparison-1789454509647/voice.local.json').read_text())['voice_id']
   payload={'text':spoken,'model_id':'eleven_v3','voice_settings':{'stability':0.5,'similarity_boost':1.0}}
   (out/'pronunciation.json').write_text(json.dumps({'displayText':text,'replacements':replacements},ensure_ascii=False,indent=2),encoding='utf8')
   (out/'request.json').write_text(json.dumps({'voice_id':voice,**payload},ensure_ascii=False,indent=2),encoding='utf8')
   req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
   with urllib.request.urlopen(req,timeout=90) as res:reply=json.load(res)
   (out/'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')));(out/'alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
   subprocess.run(['node',str(ROOT/'tmp/record-row7.mjs'),str(out),*(['--loop'] if ROW==9 else ['--current'] if ROW==8 else ['--virtual-set'] if text.startswith('Ниже по диагонали') else [])],check=True,cwd=ROOT)
   subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'tmp/mux-row3.py'),str(out)],check=True,cwd=ROOT)
   fresh=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert fresh['values'][ROW-1]==row,'Sheet changed; video saved locally'
   video=str(out/'scene.mp4');updated=[text,*row[1:9],video]
   result=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':f"'Видео'!A{ROW}:J{ROW}",'values_json':json.dumps([updated]),'value_input_option':'RAW'});assert not result.isError
   verify=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert verify['values'][ROW-1]==updated
   print(json.dumps({'video':video,'sheetVerified':True}),flush=True)
asyncio.run(main())
