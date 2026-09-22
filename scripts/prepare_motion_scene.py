"""Freeze the sheet inputs and reuse existing speech for the first Fisher scene."""
import asyncio,json,shutil,time
from pathlib import Path
from material_paths import material_dir
import av
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path('C:/GitHub/coldKode-presenter');SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
async def main():
 async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
  async with ClientSession(r,w) as c:
   await c.initialize()
   async def read(n):
    z=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':n});assert not z.isError;return json.loads(z.content[0].text)
   headers=await read('!A1:Z1')
   video_index=headers['values'][0].index('ссылка на видео');video_column=chr(65+video_index)
   sheet_range=f'!A11:{video_column}11'
   snap=await read(sheet_range);script=await read("'ФЙ-сценарий'!A1:N4")
   old=material_dir('output') / 'scene-row011-captions-1790056098495880100'
   assert json.loads((old/'request.json').read_text(encoding='utf8'))['text']==script['values'][3][0], 'Narration changed; do not reuse stale audio'
   out=material_dir()/f'scene-row011-motion-{time.time_ns()}';out.mkdir()
   save(out/'sheet-source.json',snap);save(out/'scenario-source.json',script);save(out/'sheet-headers.json',headers)
   for name in ['speech.mp3','alignment.json']:shutil.copy2(old/name,out/name)
   with av.open(str(out/'speech.mp3')) as media:duration=media.duration/av.time_base+.35
   row=snap['values'][0];v=script['values'][3]
   scenario={'version':1,'id':'fisher-initial-state','duration':duration,'canvas':{'width':1920,'height':1080,'fps':30},'diagram':{'file':'graph/draw/generated/Fisher-Yates.drawio','top':row[5],'bottom':row[6]},'code':{'placement':'right','targetLine':25,'minimumCaptionGap':24},'captions':{'anchor':{'stableId':row[5],'side':'right','offsetX':100,'offsetY':-8},'values':{'alphabet':v[1:9],'current':{'index':int(v[10]),'value':v[11]},'random':None}},'events':[{'atWord':'массив','diagramCell':'f0-n9-part-1','codeLine':26,'codeToken':'alphabet'},{'atWord':'объект','diagramCell':'f0-n5-part-1','codeLine':25,'codeToken':'current.index'}],'audioSource':str(old/'speech.mp3')}
   scenario['kind']='dual-scene'
   scenario['diagram']['rightmost']=row[7]
   scenario['sheetRange']=sheet_range
   scenario['publishRange']=f"'Видео'!{video_column}11"
   save(out/'scenario.json',scenario);print(str(out),flush=True)
asyncio.run(main())
