"""Publish a verified sequence; reject concurrent edits to scene instructions."""
import argparse,asyncio,json,hashlib
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--row',type=int,required=True);p.add_argument('--audio-column',choices=['F','G'],default='G');a=p.parse_args()
async def main():
 out=a.output.resolve();root=Path(__file__).resolve().parents[1];sheets=root.parent/'google-sheets-mcp'
 snapshot=json.loads((out/'sheet-source.json').read_text(encoding='utf8'));expected=snapshot['values'][1]
 report=json.loads((out/'sequence-report.json').read_text(encoding='utf8'));assert Path(report['video']).is_file()
 for source in json.loads((out/'scene-sources.json').read_text()):assert hashlib.sha256(Path(source['file']).read_bytes()).hexdigest()==source['sha256']
 ai=ord(a.audio_column)-ord('A');vc=chr(ord(a.audio_column)+1)
 async with stdio_client(StdioServerParameters(command=str(sheets/'.venv/Scripts/python.exe'),args=[str(sheets/'server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':snapshot['spreadsheetId'],'notation':f'!A{a.row}:{vc}{a.row}'}
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   before=json.loads(result.content[0].text)['values'][0]
   assert before[:ai]==expected[:ai] and Path(before[ai]).resolve()==out/'speech.mp3'
   assert len(before)<=ai+1 or not before[ai+1] or before[ai+1]==report['video']
   result=await c.call_tool('update_cells',{'spreadsheet_id':snapshot['spreadsheetId'],'range_a1':"'"+snapshot['sheetTitle'].replace("'","''")+f"'!{vc}{a.row}",'values_json':json.dumps([[report['video']]]),'value_input_option':'RAW'});assert not result.isError
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   after=json.loads(result.content[0].text)['values'][0];assert after[:ai+1]==before[:ai+1] and after[ai+1]==report['video']
   print(json.dumps({'video':report['video'],'verifiedRange':params['notation']}))
asyncio.run(main())
