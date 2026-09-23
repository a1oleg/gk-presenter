import asyncio,json,shutil,time
from pathlib import Path
from material_paths import material_dir
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
 old=material_dir()/'scene-row023-1789627428649969900'
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':'!A21:O21'})
   assert not result.isError
   snap=json.loads(result.content[0].text)
 request=json.loads((old/'request.json').read_text(encoding='utf8'))
 assert request['text'].strip()==snap['values'][0][0].strip()
 out=material_dir()/f'scene-row021-background-{time.time_ns()}';out.mkdir()
 for name in ['request.json','alignment.json','speech.mp3']:shutil.copy2(old/name,out/name)
 shutil.copy2(snap['values'][0][2],out/'source.drawio')
 (out/'sheet-source.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding='utf8')
 (out/'audio-source.json').write_text(json.dumps({'video':str(old/'scene-with-pointer.mp4'),'audioUnchanged':True}),encoding='utf8')
 print(out)
asyncio.run(main())
