"""Snapshot the live row and reuse its existing audio/alignment without another TTS call."""
import asyncio,json,shutil,time,argparse
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
p=argparse.ArgumentParser();p.add_argument('--row',required=True,type=int);a=p.parse_args()
async def main():
 root=Path(__file__).resolve().parents[1];sheets=root.parent/'google-sheets-mcp'
 async with stdio_client(StdioServerParameters(command=str(sheets/'.venv/Scripts/python.exe'),args=[str(sheets/'server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':f'!A{a.row-1}:H{a.row+1}'});assert not result.isError
   data=json.loads(result.content[0].text);row=data['values'][1];audio=Path(row[6]);assert audio.is_file()
   request=json.loads((audio.parent/'request.json').read_text(encoding='utf8'));assert request['text']==row[0],'Narration changed: do not reuse audio'
   out=root/'output'/f'scene-row{a.row:03d}-retake-{time.time_ns()}';out.mkdir()
   for name in ['speech.mp3','alignment.json','request.json']:shutil.copyfile(audio.parent/name,out/name)
   (out/'sheet-source.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
   print(str(out))
asyncio.run(main())
