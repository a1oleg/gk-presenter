"""Snapshot a current sheet row and reuse its existing narration without TTS."""
import asyncio,json,sys,time,shutil,hashlib
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from material_paths import material_dir
row=int(sys.argv[1])
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   async def read(notation):
    result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':'1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw','notation':notation})
    assert not result.isError
    return json.loads(result.content[0].text)
   headers=(await read('!A1:Z1'))['values'][0]
   voice=headers.index('голос');link=headers.index('ссылка на видео')
   snapshot=await read(f'!A{row}:{chr(65+voice)}{row}')
   video=Path((await read(f'!{chr(65+link)}{row}'))['values'][0][0])
 source=video.parent
 request=json.loads((source/'request.json').read_text(encoding='utf8'))
 if (source/'repair-report.json').exists():
  repair=json.loads((source/'repair-report.json').read_text(encoding='utf8'))
  if repair.get('correctedText'):request['text']=repair['correctedText']
 assert request['text'].strip()==snapshot['values'][0][0].strip(),'Narration does not match current text'
 out=material_dir()/f'scene-row{row:03d}-reuse-{time.time_ns()}';out.mkdir()
 audio=source/'speech.wav' if (source/'speech.wav').exists() else source/'speech.mp3'
 shutil.copy2(audio,out/audio.name)
 if (source/'alignment.json').exists():shutil.copy2(source/'alignment.json',out/'alignment.json')
 (out/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf8')
 (out/'sheet-source.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf8')
 report={'sourceVideo':str(video),'sourceAudio':str(audio),'audioSha256':hashlib.sha256((out/audio.name).read_bytes()).hexdigest(),'ttsRequested':False}
 (out/'audio-reuse.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(str(out))
asyncio.run(main())
