from material_paths import material_dir
"""Capture current video links without modifying the narration sheet."""
import asyncio,json,sys,time
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]
async def main():
    async with stdio_client(StdioServerParameters(command=str(ROOT.parent/'google-sheets-mcp/.venv/Scripts/python.exe'),args=[str(ROOT.parent/'google-sheets-mcp/server.py')])) as (r,w):
        async with ClientSession(r,w) as c:
            await c.initialize()
            res=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':'!A1:K100'})
            assert not res.isError
            data=json.loads(res.content[0].text)
            path=material_dir('output')/f'ready-scenes-{time.time_ns()}.json'
            path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
            rows=[i+1 for i,row in enumerate(data['values']) if i and len(row)>7 and row[7]]
            print(json.dumps({'snapshot':str(path),'rows':rows}))
asyncio.run(main())
