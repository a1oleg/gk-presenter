import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio,json,time,shutil,subprocess,hashlib
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/coldKode-presenter');SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':SID,'notation':'!A1:J3'}
   data=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text)
   row=data['values'][2];old=Path(row[9]).parent
   request=json.loads((old/'request.json').read_text(encoding='utf8'));assert request['text'].strip()==row[0].strip()
   out=material_dir('output')/f'scene-row003-retake-{time.time_ns()}';out.mkdir()
   for name in ['speech.mp3','alignment.json','request.json']:shutil.copyfile(old/name,out/name)
   assert hashlib.sha256((old/'speech.mp3').read_bytes()).digest()==hashlib.sha256((out/'speech.mp3').read_bytes()).digest()
   (out/'sheet-source.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
   print('OUTPUT='+str(out),flush=True)
   subprocess.run(['node',str(ROOT/'tmp/record-row3-fixed.mjs'),str(out)],check=True,cwd=ROOT)
   subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'tmp/mux-row3.py'),str(out)],check=True,cwd=ROOT)
   fresh=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert fresh['values'][2]==row,'Sheet changed; new video saved locally'
   video=str(out/'scene.mp4')
   result=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'Видео'!J3",'values_json':json.dumps([[video]]),'value_input_option':'RAW'});assert not result.isError
   verified=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert verified['values'][2][:9]==row[:9] and verified['values'][2][9]==video
   print(json.dumps({'video':video,'audioUnchanged':True,'sheetVerified':True}),flush=True)
asyncio.run(main())
