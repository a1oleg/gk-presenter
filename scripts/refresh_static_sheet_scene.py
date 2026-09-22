from material_paths import material_dir
"""Replace the screenshot only; retain the existing audio link and guard sheet edits.

Run with google-sheets-mcp's Python. Current columns: B scene, C cursor,
D interactive, F audio, G video. No synthesis call is made.
"""
import argparse,asyncio,json,subprocess,time,shutil
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

p=argparse.ArgumentParser();p.add_argument('--row',type=int,required=True);p.add_argument('--pointer-plan',type=Path);args=p.parse_args()
ROOT=Path(__file__).resolve().parents[1];SHEETS=ROOT.parent/'google-sheets-mcp'
SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
async def main():
 async with stdio_client(StdioServerParameters(command=str(SHEETS/'.venv/Scripts/python.exe'),args=[str(SHEETS/'server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':SID,'notation':f'!A{args.row}:G{args.row}'}
   result=await c.call_tool('get_sheet_data_by_notation',params)
   if result.isError:raise RuntimeError(str(result.content))
   snapshot=json.loads(result.content[0].text);values=snapshot['values'][0]
   assert values[2:4]==(['да','нет'] if args.pointer_plan else ['нет','нет']),'Scene flags do not match requested rendering mode'
   source=Path(values[1].strip().strip('"'));audio=Path(values[5]);assert source.is_file() and audio.is_file()
   out=material_dir('output')/f'scene-row{args.row:03d}-background-{time.time_ns()}';out.mkdir()
   (out/'sheet-source.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf8')
   if args.pointer_plan:
    shutil.copyfile(audio,out/'speech.mp3')
    shutil.copyfile(audio.parent/'alignment.json',out/'alignment.json')
    subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'scripts/animate_scene_pointer.py'),str(out),'--plan',str(args.pointer_plan.resolve()),'--background',str(source)],check=True)
   else:
    subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'scripts/render_static_scene.py'),str(out),'--row-index','0','--audio',str(audio)],check=True)
   fresh=await c.call_tool('get_sheet_data_by_notation',params)
   assert json.loads(fresh.content[0].text)['values']==snapshot['values'],'Sheet changed; result saved without updating link'
   video=str(out/('scene-with-pointer.mp4' if args.pointer_plan else 'scene-static.mp4'))
   update=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'"+snapshot['sheetTitle'].replace("'","''")+f"'!G{args.row}",'values_json':json.dumps([[video]]),'value_input_option':'RAW'})
   if update.isError:raise RuntimeError(str(update.content))
   verify=json.loads((await c.call_tool('get_sheet_data_by_notation',params)).content[0].text)['values'][0]
   assert verify[:6]==values[:6] and verify[6]==video
   print(json.dumps({'video':video,'audioUnchanged':str(audio),'sheetVerified':True}))
asyncio.run(main())
