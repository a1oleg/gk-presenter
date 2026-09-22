from material_paths import material_dir
"""Map completed videos in the narration sheet to their existing metadata folders."""
import asyncio, json, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]
SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
OUT=material_dir('output')/'scene-metadata-folder-links'

if '--plan' in sys.argv:
    data=json.loads((OUT/'before.json').read_text(encoding='utf8'))
    plan=[]
    for index,row in enumerate(data['values'][1:],start=2):
        if len(row)<8 or not row[7]: continue
        video=Path(row[7].strip().strip('"'))
        assert video.suffix.lower()=='.mp4' and video.is_file(),f'Missing completed video at row {index}'
        folder=video.parent
        metadata=sorted(p.name for p in folder.glob('*.json') if any(word in p.name for word in ('report','scene','assembly','markers','trim')))
        assert metadata,f'No scene metadata at row {index}'
        for name in metadata: json.loads((folder/name).read_text(encoding='utf-8-sig'))
        plan.append({'row':index,'video':str(video),'folder':str(folder),'metadata':metadata})
    (OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(plan,ensure_ascii=False))
    sys.exit(0)

async def main():
    async with stdio_client(StdioServerParameters(command=str(ROOT.parent/'google-sheets-mcp/.venv/Scripts/python.exe'),args=[str(ROOT.parent/'google-sheets-mcp/server.py')])) as (r,w):
        async with ClientSession(r,w) as c:
            await c.initialize()
            async def call(name,params):
                result=await c.call_tool(name,params)
                assert not result.isError,str(result)
                return json.loads(result.content[0].text)
            params={'spreadsheet_id':SID,'notation':'!A1:K100'}
            data=await call('get_sheet_data_by_notation',params)
            OUT.mkdir(parents=True,exist_ok=True)
            if '--apply' not in sys.argv:
                (OUT/'before.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
                print(json.dumps({'sheet':data['sheetTitle'],'rows':[
                    {'row':i+1,'cells':{chr(65+j):v for j,v in enumerate(row) if j!=0},'text':str(row[0])[:75] if row else ''}
                    for i,row in enumerate(data['values']) if row]},ensure_ascii=False))
                return
            plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'))
            before=json.loads((OUT/'before.json').read_text(encoding='utf8'))
            assert data['values']==before['values'],'Sheet changed since review'
            for item in plan:
                folder=Path(item['folder'])
                assert folder.is_dir() and Path(item['video']).is_file()
                assert all((folder/name).is_file() for name in item['metadata'])
            updates=[{'range':"'"+data['sheetTitle'].replace("'","''")+f"'!B{item['row']}",'values':[[item['folder']]]} for item in plan]
            await call('batch_update_cells',{'spreadsheet_id':SID,'updates_json':json.dumps(updates,ensure_ascii=False),'value_input_option':'RAW'})
            after=await call('get_sheet_data_by_notation',params)
            expected={item['row']:item['folder'] for item in plan}
            for i,row in enumerate(before['values']):
                old=(row+['']*11)[:11]
                new=(after['values'][i]+['']*11)[:11]
                if i+1 in expected: old[1]=expected[i+1]
                assert new==old,f'Unexpected change at row {i+1}'
            (OUT/'after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2),encoding='utf8')
            print(json.dumps({'verified':True,'updatedRows':list(expected),'otherCellsPreserved':True}))

asyncio.run(main())
