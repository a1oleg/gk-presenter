"""Snapshot scenario rows; synthesize missing paragraphs once, without paid retries."""
import asyncio,base64,json,shutil,time,urllib.request,sys
from pathlib import Path
from material_paths import material_dir
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]
SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
async def main():
 out=Path(sys.argv[1]) if len(sys.argv)>1 else material_dir()/f'fisher-sequence-A1-N9-{time.time_ns()}'
 out.mkdir(exist_ok=True)
 if not (out/'scenario-source.json').exists():
  async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
   async with ClientSession(r,w) as c:
    await c.initialize()
    for notation,name in [("'ФЙ-сценарий'!A1:N9",'scenario-source.json'),('!A11:Z11','sheet-source.json'),('!A1:Z1','sheet-headers.json')]:
     result=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':notation})
     assert not result.isError;save(out/name,json.loads(result.content[0].text))
 print('OUTPUT='+str(out),flush=True)
 rows=json.loads((out/'scenario-source.json').read_text(encoding='utf8'))['values']
 old=ROOT/'output/scene-row011-captions-1790056098495880100'
 voice=json.loads((old/'request.json').read_text(encoding='utf8'))['voice_id']
 entries=dict(line.split('=',1) for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
 key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
 fixes={'подстветки':'подсветки','подобнее':'подробнее','на на шестое':'на шестое','на новую проход':'на новый проход'}
 for number,row in enumerate(rows[3:],4):
  part=out/f'row-{number:02d}';part.mkdir(exist_ok=True)
  text=row[0].strip()
  for a,b in fixes.items():text=text.replace(a,b)
  if text.endswith('буква Ж'):text+='э.'
  payload={'text':text,'model_id':'eleven_v3','voice_settings':{'stability':.5,'similarity_boost':1.0}}
  if (part/'speech.mp3').exists():continue
  if number==4 and text==json.loads((old/'request.json').read_text(encoding='utf8'))['text']:
   for name in ['speech.mp3','alignment.json','request.json']:shutil.copy2(old/name,part/name)
   print(f'ROW {number}: reused',flush=True);continue
  assert not (part/'request.json').exists(),f'Row {number} already attempted; inspect before another paid call'
  save(part/'request.json',{'voice_id':voice,**payload});save(part/'text-edits.json',{'original':row[0],'spoken':text})
  request=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
  with urllib.request.urlopen(request,timeout=120) as response:reply=json.load(response)
  audio=base64.b64decode(reply.pop('audio_base64'))
  save(part/'alignment.json',reply);(part/'speech.mp3').write_bytes(audio)
  print(f'ROW {number}: generated {len(text)} characters',flush=True)
asyncio.run(main())
