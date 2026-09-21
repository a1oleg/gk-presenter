import asyncio,json,sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
 out=Path(sys.argv[1]).resolve();snap=json.loads((out/'sheet-source.json').read_text(encoding='utf8'));old=snap['values'][8]
 text=json.loads((out/'pronunciation.json').read_text(encoding='utf8'))['displayText'];assert (out/'video-check.json').exists()
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();p={'spreadsheet_id':snap['spreadsheetId'],'notation':'!A9:J9'}
   async def read():return json.loads((await c.call_tool('get_sheet_data_by_notation',p)).content[0].text)['values'][0]
   assert await read()==old
   updated=[text,*old[1:9],str(out/'scene.mp4')]
   result=await c.call_tool('update_cells',{'spreadsheet_id':p['spreadsheet_id'],'range_a1':"'Видео'!A9:J9",'values_json':json.dumps([updated]),'value_input_option':'RAW'});assert not result.isError
   assert await read()==updated;print('J9 verified')
asyncio.run(main())
