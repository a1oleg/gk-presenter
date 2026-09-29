"""Snapshot current video links in sheet order, without changing the sheet."""
import asyncio,json,time,re
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from material_paths import material_dir
async def main():
    async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
        async with ClientSession(r,w) as c:
            await c.initialize()
            result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':'!A1:P1000'})
            assert not result.isError
            data=json.loads(result.content[0].text)
    column=data['values'][0].index('ссылка на видео')
    videos=[{'row':i+1,'file':row[column].strip().strip('"')} for i,row in enumerate(data['values']) if i and len(row)>column and row[column].strip()]
    for v in videos:v['file']=re.sub(r'^/([A-Za-z]:/)',r'\1',v['file'])
    missing=[v for v in videos if not Path(v['file']).is_file()]
    assert not missing,missing
    out=material_dir()/f'montage-source-{time.time_ns()}'
    out.mkdir()
    (out/'sheet-source.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'snapshot':str(out/'sheet-source.json'),'videos':videos},ensure_ascii=False))
asyncio.run(main())
