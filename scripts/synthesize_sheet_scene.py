"""One paid TTS request with character alignment, using a row read through MCP.

Run with google-sheets-mcp's Python. No automatic paid retries.
"""
import argparse,asyncio,base64,json,sys,time,urllib.request,urllib.error
from pathlib import Path
from material_paths import material_dir
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[1]
SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
SHEETS=ROOT.parent/'google-sheets-mcp'
parser=argparse.ArgumentParser()
parser.add_argument('--row',type=int,default=3)
parser.add_argument('--audio-only',action='store_true')
parser.add_argument('--model',choices=['eleven_multilingual_v2','eleven_v3'],default='eleven_multilingual_v2')
parser.add_argument('--voice-file',type=Path,default=ROOT/'output/elevenlabs-maono-new-clone.local.json')
parser.add_argument('--text-file',type=Path,help='Explicit spoken-text override; sheet snapshot is still preserved and guarded')
parser.add_argument('--audio-column',choices=['B','C','D','E','F','G'],default='B')
parser.add_argument('--replace-audio',type=Path,help='Allow replacing only this exact existing audio link')
args=parser.parse_args()
if args.row<2: parser.error('row must be at least 2')
notation=f'!A{args.row-1}:{chr(max(ord("C"),ord(args.audio_column)+1))}{args.row+1}'

async def main():
 async with stdio_client(StdioServerParameters(command=str(SHEETS/'.venv/Scripts/python.exe'),args=[str(SHEETS/'server.py')])) as (r,w):
  async with ClientSession(r,w) as client:
   await client.initialize()
   result=await client.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':notation})
   if result.isError: raise RuntimeError(str(result.content))
   data=json.loads(result.content[0].text)
   rows=data['values']
   previous,text=rows[0][0],rows[1][0]
   following=rows[2][0] if len(rows)>2 and rows[2] else ''
   if args.text_file: text=args.text_file.read_text(encoding='utf-8-sig').strip()
   audio_index=ord(args.audio_column)-ord('A')
   assert len(rows[1])<=audio_index or not rows[1][audio_index] or (args.replace_audio and Path(rows[1][audio_index]).resolve()==args.replace_audio.resolve()), f'{args.audio_column}{args.row} already populated; inspect before generating again'
   assert text.strip(), 'Empty narration'
   scene=None
   if not args.audio_only:
    scene=Path(rows[1][2]); assert scene.is_file() and scene.suffix=='.drawio'
   out=material_dir()/f'scene-row{args.row:03d}-{time.time_ns()}'
   out.mkdir()
   (out/'sheet-source.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
   if scene: (out/'source.drawio').write_bytes(scene.read_bytes())
   entries=dict(line.split('=',1) for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in line and not line.lstrip().startswith('#'))
   key=entries['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
   voice=json.loads(args.voice_file.read_text(encoding='utf-8'))['voice_id']
   payload={'text':text,'previous_text':previous,'next_text':following,'model_id':'eleven_multilingual_v2','voice_settings':{'stability':0.5,'similarity_boost':1.0,'style':0,'use_speaker_boost':True}}
   if args.model=='eleven_v3':
    # v3 uses Natural stability; adjacent-text conditioning and speaker boost
    # are not supported. Preserve adjacent text in the sheet snapshot only.
    payload={'text':text,'model_id':args.model,'voice_settings':{'stability':0.5,'similarity_boost':1.0}}
   (out/'request.json').write_text(json.dumps({'voice_id':voice,**payload},ensure_ascii=False,indent=2),encoding='utf-8')
   print('OUTPUT='+str(out),flush=True)
   request=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',data=json.dumps(payload).encode(),headers={'xi-api-key':key,'Content-Type':'application/json'},method='POST')
   try:
    with urllib.request.urlopen(request,timeout=90) as response:
     reply=json.load(response)
     cost=response.headers.get('character-cost')
     request_id=response.headers.get('request-id')
   except urllib.error.HTTPError as e:
    raise SystemExit(f'TTS HTTP {e.code}; no retry. '+e.read().decode().replace(key,'[REDACTED]')[:300])
   audio=out/'speech.mp3'
   audio.write_bytes(base64.b64decode(reply.pop('audio_base64')))
   (out/'alignment.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2),encoding='utf-8')
   report={'audio':str(audio),'scene':str(scene) if scene else None,'output':str(out),'characterCost':cost,'requestId':request_id,'characters':len(text)}
   (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
   current=await client.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':notation})
   if json.loads(current.content[0].text)['values']!=rows: raise SystemExit(f'Sheet changed: audio saved; {args.audio_column}{args.row} not overwritten')
   result=await client.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':"'"+data['sheetTitle'].replace("'","''")+f"'!{args.audio_column}{args.row}",'values_json':json.dumps([[str(audio)]]),'value_input_option':'RAW'})
   if result.isError: raise RuntimeError(str(result.content))
   print(json.dumps(report),flush=True)

if __name__=='__main__': asyncio.run(main())
