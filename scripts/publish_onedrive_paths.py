"""Rewrite only existing material links; preserve all unrelated sheet content."""
import asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1];SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   async def read():
    response=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':'!A1:M982'})
    assert not response.isError;return json.loads(response.content[0].text)
   original=await read();values=original['values'];updates=[];missing=[]
   for row,cells in enumerate(values,1):
    for col,value in enumerate(cells):
     if not isinstance(value,str):continue
     normalized=value.replace('/','\\')
     if not any(normalized.lower().startswith(str(ROOT/kind).lower()+'\\') for kind in ['data','output']):continue
     target=Path(value).resolve();address=f'{chr(65+col)}{row}'
     if not target.exists():missing.append({'cell':address,'path':value});continue
     assert str(target).lower().startswith('c:\\users\\a1ole\\onedrive\\coldkode-presenter\\')
     updates.append({'range':f"'Видео'!{address}",'values':[[str(target)]]})
   (ROOT/'tmp/onedrive-sheet-before.json').write_text(json.dumps(original,ensure_ascii=False,indent=2),encoding='utf8')
   assert (await read())['values']==values,'Sheet changed during migration'
   if updates:
    response=await c.call_tool('batch_update_cells',{'spreadsheet_id':SID,'updates_json':json.dumps(updates),'value_input_option':'RAW'})
    assert not response.isError
   after=(await read())['values']
   expected=[list(row) for row in values]
   for change in updates:
    cell=change['range'].split('!')[1];expected[int(cell[1:])-1][ord(cell[0])-65]=change['values'][0][0]
   assert after==expected,'Unexpected table changes'
   report={'updated':len(updates),'updates':updates,'missing':missing}
   (ROOT/'tmp/onedrive-sheet-migration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
   print(json.dumps({'updated':len(updates),'missing':missing},ensure_ascii=False))
asyncio.run(main())
