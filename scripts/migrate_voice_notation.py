"""Explicit one-off migration to model.voice notation; preserve unrelated cells."""
import asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   async def read(n):
    result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':n})
    assert not result.isError
    return json.loads(result.content[0].text)['values']
   async def write(n,v):
    result=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'Видео'!"+n,'values_json':json.dumps(v,ensure_ascii=False),'value_input_option':'RAW'})
    assert not result.isError
   original=await read('!F2:F26')
   assert len(original)==25 and all(row and row[0] in ['1','2','3'] for row in original)
   updated=[[('3.3' if i==24 else '2.'+row[0])] for i,row in enumerate(original)]
   text=await read('!A26:A26')
   assert text[0][0].count('графа')==1
   accented=[[text[0][0].replace('графа','гра́фа')]]
   assert await read('!F2:F26')==original
   assert await read('!A26:A26')==text
   await write('F2:F26',updated)
   await write('A26',accented)
   assert await read('!F2:F26')==updated
   assert await read('!A26:A26')==accented
   print('Verified F2:F25=2.x, F26=3.3; A26 accented.')
asyncio.run(main())
