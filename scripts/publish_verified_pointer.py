"""Publish a verified pointer clip using current sheet headers and a guarded row."""
import argparse
import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
p.add_argument('--row', type=int, required=True)
args = p.parse_args()

def column(index):
    result = ''
    index += 1
    while index:
        index, rem = divmod(index-1, 26)
        result = chr(65+rem)+result
    return result

async def main():
    out = args.directory.resolve()
    video = out/'scene-with-pointer.mp4'
    checks = json.loads((out/'video-check.json').read_text(encoding='utf-8'))
    assert checks['allTargetsInsideFrame'] and checks['audioTrack'] and checks['sourceSceneUnchanged']
    assert checks['decodedVideoFrames'] == checks['expectedFrames'] and video.stat().st_size > 0
    snapshot = json.loads((out/'sheet-source.json').read_text(encoding='utf-8'))['scene']
    sid = snapshot['spreadsheetId']
    root = Path(__file__).resolve().parents[2]/'google-sheets-mcp'
    async with stdio_client(StdioServerParameters(command=str(root/'.venv/Scripts/python.exe'), args=[str(root/'server.py')])) as (r,w):
        async with ClientSession(r,w) as c:
            await c.initialize()
            async def read(notation):
                result = await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':sid,'notation':notation})
                assert not result.isError
                return json.loads(result.content[0].text)
            headers = (await read('!A1:Z1'))['values'][0]
            indexes = [i for i,h in enumerate(headers) if h.strip().lower() == 'ссылка на видео']
            assert len(indexes) == 1, 'Video column missing or ambiguous'
            index = indexes[0]
            assert index < 13, 'Video column moved beyond the captured snapshot; review first'
            current = await read(f'!A{args.row}:M{args.row}')
            assert current['values'] == snapshot['values'], 'Row changed after preparation'
            target = "'"+current['sheetTitle'].replace("'","''")+f"'!{column(index)}{args.row}"
            result = await c.call_tool('update_cells',{'spreadsheet_id':sid,'range_a1':target,'values_json':json.dumps([[str(video)]]),'value_input_option':'RAW'})
            assert not result.isError
            after = await read(f'!A{args.row}:M{args.row}')
            expected = list(current['values'][0])
            while len(expected) <= index: expected.append('')
            expected[index] = str(video)
            assert after['values'][0] == expected
            (out/'publication.json').write_text(json.dumps({'spreadsheetId':sid,'range':target,'video':str(video),'previousVideo':current['values'][0][index]},ensure_ascii=False,indent=2),encoding='utf-8')
            print('Published and verified: '+column(index)+str(args.row))

asyncio.run(main())
