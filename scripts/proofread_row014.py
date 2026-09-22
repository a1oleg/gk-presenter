"""Correct only the agreed narration cell, with a concurrent-edit guard."""
import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    repo = Path(__file__).resolve().parents[2] / 'google-sheets-mcp'
    sid = '1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
    async with stdio_client(StdioServerParameters(command=str(repo/'.venv/Scripts/python.exe'), args=[str(repo/'server.py')])) as (r,w):
        async with ClientSession(r,w) as c:
            await c.initialize()
            async def read():
                result = await c.call_tool('get_sheet_data_by_notation', {'spreadsheet_id':sid,'notation':'!A14:M14'})
                assert not result.isError
                return json.loads(result.content[0].text)
            before = await read()
            old = before['values'][0][0]
            corrected = old.replace('отметить что','отметить, что').replace('уникальное id, которое','уникальный ID, который').replace('не штучно а','не штучно, а')
            assert (await read())['values'] == before['values']
            result = await c.call_tool('update_cells', {'spreadsheet_id':sid,'range_a1':"'"+before['sheetTitle'].replace("'","''")+"'!A14",'values_json':json.dumps([[corrected]]),'value_input_option':'RAW'})
            assert not result.isError
            after = await read()
            assert after['values'][0] == [corrected,*before['values'][0][1:]]
            print('A14 corrected; B14:M14 unchanged')

asyncio.run(main())
