import asyncio,json,subprocess,sys
from pathlib import Path
import av,imageio_ffmpeg
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
out=Path(sys.argv[1]).resolve();scene=json.loads((out/'scenario.json').read_text(encoding='utf8'));prep=json.loads((out/'scene-preparation.json').read_text(encoding='utf8'));video=out/'scene.mp4'
assert scene['code']['layout']['safe']
ff=imageio_ffmpeg.get_ffmpeg_exe()
if not video.exists():
 subprocess.run([ff,'-nostdin','-n','-hide_banner','-loglevel','error','-i',prep['recording'],'-framerate','30','-i',str(out/'caption-frames/%05d.png'),'-i',str(out/'speech.mp3'),'-filter_complex','[0:v]fps=30,setsar=1[v];[v][1:v]overlay=0:0:format=auto[out]','-map','[out]','-map','2:a','-af','apad','-t',str(scene['duration']),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(video)],check=True)
with av.open(str(video)) as media:
 assert (media.streams.video[0].width,media.streams.video[0].height)==(1920,1080)
 frames=0
 for frame in media.decode(video=0):
  frames+=1
 assert abs(frames/30-scene['duration'])<.15
with av.open(str(video)) as media:assert sum(f.samples for f in media.decode(audio=0))>0
report={'video':str(video),'seconds':frames/30,'frames':frames,'captions':'Motion Canvas 3.17.2','voice':'3.3 (reused)','layout':scene['code']['layout'],'pointerEvents':len(prep['events']),'cameraPreserved':prep['cameraBefore']['camera']==prep['cameraAfter']['camera']}
(out/'video-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
async def publish():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize();snap=json.loads((out/'sheet-source.json').read_text(encoding='utf8'));sid=snap['spreadsheetId']
   async def read(n):return json.loads((await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':sid,'notation':n})).content[0].text)
   assert (await read('!A11:K11'))['values']==snap['values'],'Sheet changed; video not published'
   assert (await read("'ФЙ-сценарий'!A1:N4"))['values']==json.loads((out/'scenario-source.json').read_text(encoding='utf8'))['values']
   result=await c.call_tool('update_cells',{'spreadsheet_id':sid,'range_a1':"'Видео'!K11",'values_json':json.dumps([[str(video)]]),'value_input_option':'RAW'});assert not result.isError
   assert (await read('!K11'))['values']==[[str(video)]];print(json.dumps(report,ensure_ascii=False))
asyncio.run(publish())
