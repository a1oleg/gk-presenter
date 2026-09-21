import argparse,asyncio,json,subprocess
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
p=argparse.ArgumentParser();p.add_argument('out',type=Path);args=p.parse_args();out=args.out.resolve();root=Path('C:/GitHub/coldKode-presenter')
async def main():
 snapshot=json.loads((out/'sheet-source.json').read_text(encoding='utf8'))
 request=json.loads((out/'request.json').read_text(encoding='utf8'))
 report=json.loads((out/'video-check.json').read_text(encoding='utf8'))
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':snapshot['spreadsheetId'],'notation':'!A1:J3'}
   fresh=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text)
   assert fresh['values'][2]==snapshot['values'][2] and fresh['values'][0]==snapshot['values'][0],'Sheet changed'
   # One row write preserves all scene controls; only punctuation and output link change.
   row=[request['text'],*fresh['values'][2][1:9],report['video']]
   result=await c.call_tool('update_cells',{'spreadsheet_id':snapshot['spreadsheetId'],'range_a1':"'Видео'!A3:J3",'values_json':json.dumps([row]),'value_input_option':'RAW'});assert not result.isError
   verify=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text);assert verify['values'][2]==row
   print(json.dumps({'video':report['video'],'sheetVerified':True},ensure_ascii=False))
asyncio.run(main())
