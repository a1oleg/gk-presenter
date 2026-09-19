"""Fill an empty scene cell with a semantic head; never replace another scene."""
import argparse, asyncio, json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
p=argparse.ArgumentParser();p.add_argument('--row',type=int,required=True);p.add_argument('--stable-id',required=True);a=p.parse_args()
async def main():
 root=Path(__file__).resolve().parents[2]/'google-sheets-mcp'
 async with stdio_client(StdioServerParameters(command=str(root/'.venv/Scripts/python.exe'),args=[str(root/'server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':f'!A{a.row}:H{a.row}'}
   response=await c.call_tool('get_sheet_data_by_notation',params);assert not response.isError
   data=json.loads(response.content[0].text);before=data['values'][0]
   assert not before[1] or before[1]==a.stable_id,'Scene already supplied: refusing overwrite'
   result=await c.call_tool('update_cells',{'spreadsheet_id':params['spreadsheet_id'],'range_a1':"'"+data['sheetTitle'].replace("'","''")+f"'!B{a.row}",'values_json':json.dumps([[a.stable_id]]),'value_input_option':'RAW'});assert not result.isError
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   after=json.loads(result.content[0].text)['values'][0];expected=before.copy();expected[1]=a.stable_id;assert after==expected
   print(json.dumps({'row':a.row,'stableId':a.stable_id,'verified':True}))
asyncio.run(main())
