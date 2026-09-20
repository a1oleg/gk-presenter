"""Read or narrowly replace the requested narration column via the Sheets MCP."""
import asyncio, json, sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SID = '1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
OUT = ROOT / 'output' / 'model-stub-chapter'

async def main():
    async with stdio_client(StdioServerParameters(
        command=str(ROOT.parent / 'google-sheets-mcp/.venv/Scripts/python.exe'),
        args=[str(ROOT.parent / 'google-sheets-mcp/server.py')],
    )) as (r, w):
        async with ClientSession(r, w) as client:
            await client.initialize()
            async def call(name, params):
                result = await client.call_tool(name, params)
                assert not result.isError, str(result)
                return json.loads(result.content[0].text)
            params = {'spreadsheet_id': SID, 'notation': '!A26:H48'}
            snapshot = await call('get_sheet_data_by_notation', params)
            if '--apply' not in sys.argv:
                OUT.mkdir(parents=True, exist_ok=True)
                (OUT / 'before.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf8')
                print(json.dumps({'sheet':snapshot['sheetTitle'], 'rows':[
                    {'row':26+i, 'text': row[0] if row else '', 'otherColumns':row[1:3]}
                    for i,row in enumerate(snapshot['values'])]}, ensure_ascii=False))
                return
            before = json.loads((OUT / 'before.json').read_text(encoding='utf8'))
            assert snapshot['values'] == before['values'], 'Sheet changed since review'
            texts = json.loads((ROOT / 'scenes/model-stub-chapter.json').read_text(encoding='utf8'))
            end = 32 + len(texts)
            await call('update_cells', {'spreadsheet_id': SID,
                'range_a1': "'"+snapshot['sheetTitle'].replace("'", "''")+f"'!A33:A{end}",
                'values_json': json.dumps([[text] for text in texts], ensure_ascii=False), 'value_input_option': 'RAW'})
            after = await call('get_sheet_data_by_notation', params)
            for i in range(max(len(before['values']),len(after['values']))):
                old = (before['values'][i] if i<len(before['values']) else []) + ['']*8
                new = (after['values'][i] if i<len(after['values']) else []) + ['']*8
                assert new[1:8] == old[1:8], f'Other columns changed at row {26+i}'
                assert new[0] == (texts[i-7] if 7<=i<7+len(texts) else old[0])
            (OUT / 'after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding='utf8')
            print(json.dumps({'updated':f'A33:A{end}', 'verified':True, 'otherColumnsPreserved':True},ensure_ascii=False))

asyncio.run(main())
