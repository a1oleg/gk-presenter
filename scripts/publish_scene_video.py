"""Publish a verified local clip path without overwriting changed sheet content."""
import argparse,asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--row',type=int,required=True);p.add_argument('--suffix',default='');p.add_argument('--replace-video',type=Path);args=p.parse_args()
async def main():
 root=Path(__file__).resolve().parents[1];sheets=root.parent/'google-sheets-mcp'
 snapshot=json.loads((args.directory/'sheet-source.json').read_text(encoding='utf8'))
 report=json.loads((args.directory/f'interactive-video-report{args.suffix}.json').read_text(encoding='utf8'))
 assert Path(report['video']).is_file()
 async with stdio_client(StdioServerParameters(command=str(sheets/'.venv/Scripts/python.exe'),args=[str(sheets/'server.py')])) as (r,w):
  async with ClientSession(r,w) as client:
   await client.initialize()
   params={'spreadsheet_id':snapshot['spreadsheetId'],'notation':f'!A{args.row}:E{args.row}'}
   current=await client.call_tool('get_sheet_data_by_notation',params)
   if current.isError: raise RuntimeError(str(current.content))
   values=json.loads(current.content[0].text)['values'][0]
   expected=snapshot['values'][1]
   assert (values+['']*3)[:3]==(expected+['']*3)[:3], 'Narration/scene changed'
   assert len(values)<5 or not values[4] or values[4]==report['video'] or (args.replace_video and Path(values[4]).resolve()==args.replace_video.resolve()), 'Video already exists'
   assert Path(values[3]).resolve()==(args.directory/'speech.mp3').resolve(), 'Audio changed'
   result=await client.call_tool('update_cells',{'spreadsheet_id':snapshot['spreadsheetId'],'range_a1':"'"+snapshot['sheetTitle'].replace("'","''")+f"'!E{args.row}",'values_json':json.dumps([[report['video']]]),'value_input_option':'RAW'})
   if result.isError: raise RuntimeError(str(result.content))
   check=await client.call_tool('get_sheet_data_by_notation',params)
   assert json.loads(check.content[0].text)['values'][0][4]==report['video']
   print(f'Verified D{args.row}:E{args.row}')
asyncio.run(main())
