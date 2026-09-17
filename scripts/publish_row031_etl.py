"""Replace only A31 with the requested ETL chapter, preserving scene settings."""
import asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();p={'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':'!A31:H31'}
   res=await c.call_tool('get_sheet_data_by_notation',p);assert not res.isError
   d=json.loads(res.content[0].text);before=d['values'][0]
   expected='Перейдём к Claude Code.\nЭто React-о-подобное приложение на TypeScript, весом чуть больше полумиллиона строчек кода, которое нужно преобразовать в граф.'
   assert before[0]==expected,'User edited A31; do not overwrite'
   text=(ROOT/'scenes/row031-etl.narration.txt').read_text(encoding='utf8').strip()
   res=await c.call_tool('update_cells',{'spreadsheet_id':p['spreadsheet_id'],'range_a1':"'"+d['sheetTitle']+"'!A31",'values_json':json.dumps([[text]],ensure_ascii=False),'value_input_option':'RAW'});assert not res.isError
   res=await c.call_tool('get_sheet_data_by_notation',p);assert not res.isError
   assert json.loads(res.content[0].text)['values'][0]==[text,*before[1:]]
   print(json.dumps({'updated':'A31','otherCellsPreserved':True,'words':len(text.split())}))
asyncio.run(main())
