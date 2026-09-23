import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio,json,time,shutil,subprocess,os,hashlib
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/graphKoda-presenter');SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':SID,'notation':'!A1:J5'}
   data=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text)
   for rownum in range(2,6):
    row=data['values'][rownum-1];old=Path(row[9]).parent
    out=material_dir('output')/f'scene-row{rownum:03d}-1080-{time.time_ns()}';out.mkdir()
    print('OUTPUT='+str(out),flush=True)
    for name in ['speech.mp3','alignment.json','request.json']:shutil.copyfile(old/name,out/name)
    assert hashlib.sha256((old/'speech.mp3').read_bytes()).digest()==hashlib.sha256((out/'speech.mp3').read_bytes()).digest()
    (out/'sheet-source.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    def run(args,**kw):subprocess.run(args,check=True,cwd=ROOT,**kw)
    py=str(ROOT/'.venv/Scripts/python.exe')
    if rownum<5:
     run(['node',str(ROOT/'tmp/capture-batch1080.mjs'),str(out),str(rownum)])
     if rownum==3:
      run(['node',str(ROOT/'tmp/record-row3-fixed.mjs'),str(out)])
      run([py,str(ROOT/'tmp/mux-row3.py'),str(out)])
      video=out/'scene.mp4'
     else:
      run([py,str(ROOT/'scripts/render_static_scene.py'),str(out),'--background',str(out/'scene.png'),'--canvas','1920x1080'])
      video=out/'scene-static.mp4'
    else:
     shutil.copyfile(old/'source.drawio',out/'source.drawio')
     run(['node',str(ROOT/'scripts/render_drawio_scene.mjs'),str(out)],env={**os.environ,'PRESENTER_CANVAS':'1920x1080'})
     run([py,str(ROOT/'scripts/animate_scene_pointer.py'),str(out),'--plan',str(ROOT/'scenes/row005-hla.markers.json'),'--source-drawio',str(old/'source.drawio')])
     video=out/'scene-with-pointer.mp4'
    fresh=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text)
    assert fresh['values'][rownum-1]==row,'Row changed; output saved locally'
    result=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':f"'Видео'!J{rownum}",'values_json':json.dumps([[str(video)]]),'value_input_option':'RAW'});assert not result.isError
    verify=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text)
    assert verify['values'][rownum-1][9]==str(video) and verify['values'][rownum-1][:9]==row[:9]
    print(json.dumps({'row':rownum,'video':str(video),'audioUnchanged':True,'sheetVerified':True}),flush=True)
asyncio.run(main())
