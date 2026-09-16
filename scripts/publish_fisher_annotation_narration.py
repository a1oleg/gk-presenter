"""Publish the requested six narration paragraphs only; preserve all other columns."""
import asyncio,json,time
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
root=Path(__file__).resolve().parents[1]
sid='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 plan=json.loads((root/'scenes/fisher-annotation-narration.json').read_text(encoding='utf8'))
 async with stdio_client(StdioServerParameters(command=str(root.parent/'google-sheets-mcp/.venv/Scripts/python.exe'),args=[str(root.parent/'google-sheets-mcp/server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   params={'spreadsheet_id':sid,'notation':'!A16:K21'}
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   snapshot=json.loads(result.content[0].text)
   rows=snapshot['values']
   expected=['Теперь сделаем диаграммы "говорящими".','\\','','','','']
   assert [(row[0] if row else '') for row in rows]==expected,'Narration changed; do not overwrite'
   out=root/'output'/f'fisher-annotation-script-{time.time_ns()}';out.mkdir()
   (out/'before.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf8')
   fresh=await c.call_tool('get_sheet_data_by_notation',params)
   assert json.loads(fresh.content[0].text)['values']==rows,'Sheet changed'
   result=await c.call_tool('update_cells',{'spreadsheet_id':sid,'range_a1':"'"+snapshot['sheetTitle'].replace("'","''")+"'!A16:A21",'values_json':json.dumps([[t] for t in plan['paragraphs']],ensure_ascii=False),'value_input_option':'RAW'})
   assert not result.isError
   result=await c.call_tool('get_sheet_data_by_notation',params)
   after=json.loads(result.content[0].text)
   assert [row[0] for row in after['values']]==plan['paragraphs']
   assert [row[1:] for row in after['values']]==[row[1:] for row in rows]
   (out/'after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2),encoding='utf8')
   print('A16:A21 verified; B:K unchanged. Backup: '+str(out))
asyncio.run(main())
