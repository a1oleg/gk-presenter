"""Publish new scene metadata/video while retaining the original, unchanged audio link."""
import argparse,asyncio,hashlib,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--row',type=int,required=True);a=p.parse_args()
async def main():
 out=a.output.resolve();snapshot=json.loads((out/'sheet-source.json').read_text(encoding='utf8'));expected=snapshot['values'][1]
 checks=json.loads((out/'video-check.json').read_text(encoding='utf8'));assert checks['decodedVideoFrames']==checks['expectedFrames'] and checks['audioTrack']
 assert hashlib.sha256(Path(expected[6]).read_bytes()).digest()==hashlib.sha256((out/'speech.mp3').read_bytes()).digest()
 meta=out/'scene-preparation.json';video=out/'scene-with-pointer.mp4';assert meta.is_file() and video.is_file()
 sheets=Path(__file__).resolve().parents[2]/'google-sheets-mcp'
 async with stdio_client(StdioServerParameters(command=str(sheets/'.venv/Scripts/python.exe'),args=[str(sheets/'server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':snapshot['spreadsheetId'],'notation':f'!A{a.row}:H{a.row}'}
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   before=json.loads(result.content[0].text)['values'][0];assert before==expected,'Row changed'
   after=before.copy();after[1]=str(meta);after[7]=str(video)
   result=await c.call_tool('update_cells',{'spreadsheet_id':params['spreadsheet_id'],'range_a1':"'"+snapshot['sheetTitle'].replace("'","''")+f"'!B{a.row}:H{a.row}",'values_json':json.dumps([after[1:]]),'value_input_option':'RAW'});assert not result.isError
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   assert json.loads(result.content[0].text)['values'][0]==after
   print(json.dumps({'video':str(video),'metadata':str(meta),'audioUnchanged':True,'verified':True}))
asyncio.run(main())
