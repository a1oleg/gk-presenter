import asyncio,json,sys,subprocess
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
out=Path(sys.argv[1]);video=out/'scene.mp4'
row=int(sys.argv[2]) if len(sys.argv)>2 else 15
scene=json.loads((out/'scenario.json').read_text(encoding='utf8'))
probe="import av,sys,json; p=sys.argv[1]; m=av.open(p); w=m.streams.video[0].width; h=m.streams.video[0].height; n=sum(1 for f in m.decode(video=0)); m.close(); m=av.open(p); a=sum(f.samples for f in m.decode(audio=0)); print(json.dumps([w,h,n,a]))"
w,h,frames,a=json.loads(subprocess.check_output([str(Path(__file__).resolve().parents[1]/'.venv/Scripts/python.exe'),'-c',probe,str(video)],text=True))
assert (w,h)==(1920,1080) and a>0 and abs(frames/30-scene['duration'])<.15
async def main():
 snap=json.loads((out/'sheet-source.json').read_text(encoding='utf8'));sid=snap['spreadsheetId']
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   async def read(n):
    result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':sid,'notation':n});assert not result.isError;return json.loads(result.content[0].text)
   current=(await read(snap['range']))['values'];expected=snap['values']
   scenario_snapshot=out/'scenario-source.json'
   if scenario_snapshot.exists():
    linked=json.loads(scenario_snapshot.read_text(encoding='utf8'))
    assert (await read(linked['range']))['values']==linked['values'],'Linked scenario changed; no publication'
   spoken=json.loads((out/'request.json').read_text(encoding='utf8'))['text']
   assert current==expected or (current[0][1:]==expected[0][1:] and current[0][0].strip()==spoken),'Sheet changed; no publication'
   header=(await read('!A1:Z1'))['values'][0];col=header.index('ссылка на видео');assert col<26
   dest=f"'Видео'!{chr(65+col)}{row}"
   result=await c.call_tool('update_cells',{'spreadsheet_id':sid,'range_a1':dest,'values_json':json.dumps([[str(video)]]),'value_input_option':'RAW'});assert not result.isError
   assert (await read(dest))['values']==[[str(video)]]
   report={'video':str(video),'seconds':frames/30,'frames':frames,'published':dest,'voice':'3.3'}
   (out/'video-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
asyncio.run(main())
