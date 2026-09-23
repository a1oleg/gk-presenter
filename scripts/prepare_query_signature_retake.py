"""Snapshot current row 36 and reuse matching narration without a paid TTS call."""
import asyncio,json,shutil,time,sys,hashlib
from pathlib import Path
from material_paths import material_dir
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
 old=Path(sys.argv[1]).resolve()
 row=int(sys.argv[2]) if len(sys.argv)>2 else 36
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':f'!A{row}:P{row}'})
   assert not result.isError
   snapshot=json.loads(result.content[0].text)
 request=json.loads((old/'request.json').read_text(encoding='utf8'))
 assert snapshot['values'][0][0].strip()==request['text'].strip(),'Narration changed'
 out=material_dir()/f'scene-row{row:03d}-below-{time.time_ns()}';out.mkdir()
 for name in ['request.json','speech.mp3','alignment.json']:shutil.copy2(old/name,out/name)
 (out/'sheet-source.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf8')
 (out/'audio-reuse.json').write_text(json.dumps({'source':str(old/'speech.mp3'),'sha256':hashlib.sha256((out/'speech.mp3').read_bytes()).hexdigest()},indent=2),encoding='utf8')
 print(str(out))
asyncio.run(main())
