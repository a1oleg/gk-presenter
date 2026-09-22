"""Guarded spelling/punctuation correction of the current row; no other cells."""
import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SHEETS = ROOT.parent / 'google-sheets-mcp'
SID = '1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'

async def main():
    corrected = (ROOT/'scenes/row013.narration.txt').read_text(encoding='utf-8').strip()
    async with stdio_client(StdioServerParameters(command=str(SHEETS/'.venv/Scripts/python.exe'), args=[str(SHEETS/'server.py')])) as (r,w):
        async with ClientSession(r,w) as c:
            await c.initialize()
            params = {'spreadsheet_id':SID,'notation':'!A13:M13'}
            async def read():
                result = await c.call_tool('get_sheet_data_by_notation',params)
                assert not result.isError
                return json.loads(result.content[0].text)
            before = await read()
            old = before['values'][0][0]
            expected = old.replace('тому что','тому, что').replace('Сначала ,на этапе экстракции,','Сначала, на этапе экстракции,').replace('коде которые','коде, которые').replace('соответствующимим','соответствующими').replace('сохраннёным','сохранённым').replace('vs code которое','VS Code, которое').replace('интерактивный экран и','интерактивный экран, и').strip()
            assert expected == corrected, 'Text changed; review before writing'
            assert (await read())['values'] == before['values'], 'Concurrent sheet edit'
            result = await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'"+before['sheetTitle'].replace("'","''")+"'!A13",'values_json':json.dumps([[corrected]]),'value_input_option':'RAW'})
            assert not result.isError
            after = await read()
            assert after['values'][0][0] == corrected
            assert after['values'][0][1:] == before['values'][0][1:]
            print('A13 corrected and verified; B13:M13 unchanged')

asyncio.run(main())
