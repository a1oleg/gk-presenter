"""Fill an empty scene cell with a semantic head; never replace another scene."""
import argparse, asyncio, json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
p=argparse.ArgumentParser();p.add_argument('--row',type=int,required=True);p.add_argument('--stable-id',required=True);p.add_argument('--metadata-file',type=Path);a=p.parse_args()
async def main():
 root=Path(__file__).resolve().parents[2]/'google-sheets-mcp'
 async with stdio_client(StdioServerParameters(command=str(root/'.venv/Scripts/python.exe'),args=[str(root/'server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':f'!A{a.row}:H{a.row}'}
   response=await c.call_tool('get_sheet_data_by_notation',params);assert not response.isError
   data=json.loads(response.content[0].text);before=data['values'][0]
   value=a.stable_id
   if a.metadata_file:
    meta=json.loads(a.metadata_file.read_text(encoding='utf8'));assert meta['stableId']==a.stable_id
    value=str(a.metadata_file.resolve())
   assert not before[1] or before[1] in [a.stable_id,value],'Scene already supplied: refusing overwrite'
   result=await c.call_tool('update_cells',{'spreadsheet_id':params['spreadsheet_id'],'range_a1':"'"+data['sheetTitle'].replace("'","''")+f"'!B{a.row}",'values_json':json.dumps([[value]]),'value_input_option':'RAW'});assert not result.isError
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   after=json.loads(result.content[0].text)['values'][0];expected=before.copy();expected[1]=value;assert after==expected
   print(json.dumps({'row':a.row,'scene':value,'stableId':a.stable_id,'verified':True}))
asyncio.run(main())
