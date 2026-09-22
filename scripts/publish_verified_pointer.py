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
p.add_argument('--interactive', action='store_true')
p.add_argument('--repaired-tail', action='store_true')
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
    if args.interactive:
        video = out/'scene-interactive.mp4'
        checks = json.loads((out/'video-validation.json').read_text(encoding='utf-8'))
        recording = json.loads((out/'recording.json').read_text(encoding='utf-8'))
        assert recording['completed'] and checks['audioFrames'] > 0 and checks['frames'] > 0
        cameras = json.loads((out/'camera-checks.json').read_text(encoding='utf-8'))
        assert cameras and all(all(abs(c['before'][k]-c['after'][k])<1 for k in ['x','y','width','height']) for c in cameras)
    else:
        video = out/'scene-with-pointer.mp4'
        checks = json.loads((out/'video-check.json').read_text(encoding='utf-8'))
        assert checks['allTargetsInsideFrame'] and checks['audioTrack'] and checks['sourceSceneUnchanged']
        assert checks['decodedVideoFrames'] == checks['expectedFrames']
    previous_video = None
    if args.repaired_tail:
        assert args.interactive
        repair = json.loads((out/'tail-repair.json').read_text(encoding='utf-8'))
        previous_video = str(video)
        assert repair['original'] == previous_video and repair['audioFrames'] > 0
        assert repair['seconds']-repair['falseMovementCompleteBy'] >= 2
        video = Path(repair['video'])
        assert video.parent == out
    assert video.stat().st_size > 0
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
            expected_before = list(snapshot['values'][0])
            if previous_video:
                while len(expected_before) <= index: expected_before.append('')
                expected_before[index] = previous_video
            assert current['values'] == [expected_before], 'Row changed after preparation'
            target = "'"+current['sheetTitle'].replace("'","''")+f"'!{column(index)}{args.row}"
            result = await c.call_tool('update_cells',{'spreadsheet_id':sid,'range_a1':target,'values_json':json.dumps([[str(video)]]),'value_input_option':'RAW'})
            assert not result.isError
            after = await read(f'!A{args.row}:M{args.row}')
            expected = list(current['values'][0])
            while len(expected) <= index: expected.append('')
            expected[index] = str(video)
            assert after['values'][0] == expected
            (out/'publication.json').write_text(json.dumps({'spreadsheetId':sid,'range':target,'video':str(video),'previousVideo':current['values'][0][index] if len(current['values'][0])>index else ''},ensure_ascii=False,indent=2),encoding='utf-8')
            print('Published and verified: '+column(index)+str(args.row))

asyncio.run(main())
