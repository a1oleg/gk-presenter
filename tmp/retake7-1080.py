import asyncio,json,time,shutil,subprocess,hashlib
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/coldKode-presenter');SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':SID,'notation':'!A1:J7'}
   snap=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);row=snap['values'][6];old=Path(row[9]).parent
   out=ROOT/'output'/f'scene-row007-1080-{time.time_ns()}';out.mkdir();print('OUTPUT='+str(out),flush=True)
   for name in ['speech.mp3','alignment.json','request.json','pronunciation.json']:shutil.copyfile(old/name,out/name)
   assert hashlib.sha256((old/'speech.mp3').read_bytes()).digest()==hashlib.sha256((out/'speech.mp3').read_bytes()).digest()
   (out/'sheet-source.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding='utf8')
   for script in ['setup1080.mjs','record-row7.mjs']:subprocess.run(['node',str(ROOT/'tmp'/script),str(out)],check=True,cwd=ROOT)
   subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'tmp/mux-row3.py'),str(out)],check=True,cwd=ROOT)
   report=json.loads((out/'video-check.json').read_text());assert (report['width'],report['height'])==(1920,1080)
   fresh=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert fresh['values'][6]==row
   result=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'Видео'!J7",'values_json':json.dumps([[report['video']]]),'value_input_option':'RAW'});assert not result.isError
   verify=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert verify['values'][6][9]==report['video'] and verify['values'][6][:9]==row[:9]
   print(json.dumps({'video':report['video'],'audioUnchanged':True,'sheetVerified':True}),flush=True)
asyncio.run(main())
