"""Publish static video in H, guarding current A:G including Google Slides URL."""
import argparse,asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--row',type=int,required=True);a=p.parse_args()
async def main():
 out=a.output.resolve();root=Path(__file__).resolve().parents[1];sheets=root.parent/'google-sheets-mcp'
 snapshot=json.loads((out/'sheet-source.json').read_text(encoding='utf8'));expected=snapshot['values'][1]
 report=json.loads((out/'static-video-report.json').read_text(encoding='utf8'));assert Path(report['video']).is_file() and report['decodedFrames']>0 and report['audioSamples']>0
 async with stdio_client(StdioServerParameters(command=str(sheets/'.venv/Scripts/python.exe'),args=[str(sheets/'server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':snapshot['spreadsheetId'],'notation':f'!A{a.row}:H{a.row}'}
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   before=json.loads(result.content[0].text)['values'][0]
   assert before[:6]==expected[:6] and Path(before[6]).resolve()==out/'speech.mp3'
   assert len(before)<8 or not before[7] or before[7]==report['video']
   result=await c.call_tool('update_cells',{'spreadsheet_id':snapshot['spreadsheetId'],'range_a1':"'"+snapshot['sheetTitle'].replace("'","''")+f"'!H{a.row}",'values_json':json.dumps([[report['video']]]),'value_input_option':'RAW'});assert not result.isError
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   after=json.loads(result.content[0].text)['values'][0];assert after[:7]==before[:7] and after[7]==report['video']
   print(json.dumps({'video':report['video'],'sheetVerified':True}))
asyncio.run(main())
