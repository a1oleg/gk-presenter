"""Publish a checked A:G scene, preserving narration, flags, voice and audio."""
import argparse,asyncio,json,hashlib
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--row',type=int,required=True);a=p.parse_args()
async def main():
 out=a.directory.resolve();root=Path(__file__).resolve().parents[1];sheets=root.parent/'google-sheets-mcp'
 snapshot=json.loads((out/'sheet-source.json').read_text(encoding='utf8'))
 expected=snapshot['values'][1]
 checks=json.loads((out/'video-check.json').read_text(encoding='utf8'))
 assert checks['decodedVideoFrames']==checks['expectedFrames'] and checks['audioTrack']
 if (out/'scene-preparation.json').exists():
  scene=json.loads((out/'scene-preparation.json').read_text(encoding='utf8'))
  assert hashlib.sha256(Path(scene['source']).read_bytes()).hexdigest()==scene['sha256'],'Original scene changed'
 else:
  markers=json.loads((out/'markers.json').read_text(encoding='utf8'))
  assert Path(markers['sourceScene']).read_bytes()==(out/'scene.png').read_bytes(),'Screenshot changed'
 video=out/'scene-with-pointer.mp4';assert video.is_file()
 async with stdio_client(StdioServerParameters(command=str(sheets/'.venv/Scripts/python.exe'),args=[str(sheets/'server.py')])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();params={'spreadsheet_id':snapshot['spreadsheetId'],'notation':f'!A{a.row}:G{a.row}'}
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   values=json.loads(result.content[0].text)['values'][0]
   assert values[:5]==expected[:5],'Scene instructions changed'
   assert Path(values[5]).resolve()==out/'speech.mp3','Audio changed'
   assert len(values)<7 or not values[6] or values[6]==str(video),'Video already exists'
   result=await c.call_tool('update_cells',{'spreadsheet_id':snapshot['spreadsheetId'],'range_a1':"'"+snapshot['sheetTitle'].replace("'","''")+f"'!G{a.row}",'values_json':json.dumps([[str(video)]]),'value_input_option':'RAW'});assert not result.isError
   result=await c.call_tool('get_sheet_data_by_notation',params);assert not result.isError
   after=json.loads(result.content[0].text)['values'][0]
   assert after[:6]==values[:6] and after[6]==str(video)
   print(json.dumps({'video':str(video),'sheetVerified':True,'originalSceneUnchanged':True}))
asyncio.run(main())
