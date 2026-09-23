import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio,base64,json,subprocess,time,urllib.request,sys,shutil
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/graphKoda-presenter');SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
ROW=int(sys.argv[1]) if len(sys.argv)>1 else 4
POINTER='--pointer' in sys.argv
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':SID,'notation':f'!A1:J{ROW}'}
   snap=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);row=snap['values'][ROW-1]
   assert row[3]=='нет' and row[5:9]==(['1','нет','нет','3.3'] if POINTER else ['нет','нет','нет','3.3'])
   text=row[0].replace('пояснениями ,которые','пояснениями, которые').replace(' \n','\n').strip()
   if '--stress-concept' in sys.argv:text=text.replace('Concept','Co\u0301ncept')
   out=material_dir('output')/f'scene-row{ROW:03d}-{time.time_ns()}';out.mkdir()
   (out/'sheet-source.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding='utf8');print('OUTPUT='+str(out),flush=True)
   if Path(row[1]).suffix.lower()=='.drawio':
    shutil.copyfile(row[1],out/'source.drawio')
    subprocess.run(['node',str(ROOT/'scripts/render_drawio_scene.mjs'),str(out)],check=True,cwd=ROOT)
   else:
    assert ROW==4 and row[1]=='VS Code OBS'
    subprocess.run(['node',str(ROOT/'tmp/capture-row4.mjs'),str(out)],check=True,cwd=ROOT)
   env=dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'));key=env['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
   voice=json.loads((material_dir('output') / 'voice-mix-comparison-1789454509647/voice.local.json').read_text())['voice_id']
   payload={'text':text,'model_id':'eleven_v3','voice_settings':{'stability':0.5,'similarity_boost':1.0}}
   (out/'request.json').write_text(json.dumps({'voice_id':voice,**payload},ensure_ascii=False,indent=2),encoding='utf8')
   req=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
   with urllib.request.urlopen(req,timeout=90) as res:reply=json.load(res)
   (out/'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')));(out/'alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf8')
   if POINTER:
    subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'scripts/animate_scene_pointer.py'),str(out),'--plan',str(ROOT/'scenes/row005-hla.markers.json'),'--source-drawio',row[1]],check=True)
   else:
    subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'scripts/render_static_scene.py'),str(out),'--background',str(out/'scene.png'),'--canvas','1600x900'],check=True)
   fresh=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert fresh['values'][ROW-1]==row,'Sheet changed'
   video=str(out/('scene-with-pointer.mp4' if POINTER else 'scene-static.mp4'));updated=[text,*row[1:9],video]
   result=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':f"'Видео'!A{ROW}:J{ROW}",'values_json':json.dumps([updated]),'value_input_option':'RAW'});assert not result.isError
   verify=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert verify['values'][ROW-1]==updated
   print(json.dumps({'video':video,'sheetVerified':True}),flush=True)
asyncio.run(main())
