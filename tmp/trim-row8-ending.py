import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio, json, subprocess, time
from pathlib import Path
import av, imageio_ffmpeg
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path('C:/GitHub/gk-presenter')
SID='1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
ENDING='Обратите внимание, что я изменил тему подсветки синтаксиса, чтобы она сочеталась с диаграммой.'
def save(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')

async def main():
    async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe',args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
        async with ClientSession(r,w) as c:
            await c.initialize()
            async def read():
                res=await c.call_tool('get_sheet_data_by_notation',{'spreadsheet_id':SID,'notation':'!A8:J8'})
                assert not res.isError
                return json.loads(res.content[0].text)
            snapshot=await read();row=snapshot['values'][0]
            assert row[0].strip().endswith(ENDING)
            source=Path(row[9]);assert source.parent.name=='scene-row008-phonetic-1789992734904632900'
            align=json.loads((source.parent/'alignment.json').read_text(encoding='utf8'))['alignment']
            text=''.join(align['characters']);idx=text.index(ENDING)
            last=idx-1
            while text[last].isspace(): last-=1
            end=align['character_end_times_seconds'][last]
            next_start=align['character_start_times_seconds'][idx]
            cutoff=end+max(0,min(.18,(next_start-end)/2))
            assert 0<cutoff<=next_start
            out=material_dir('output')/f'scene-row008-trimmed-{time.time_ns()}';out.mkdir()
            video=out/'scene.mp4'
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-i',str(source),'-t',str(cutoff),'-map','0:v:0','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(video)],check=True)
            with av.open(str(video)) as m:
                assert (m.streams.video[0].width,m.streams.video[0].height)==(1920,1080)
                frames=sum(1 for _ in m.decode(video=0))
                assert abs(frames/30-cutoff)<.1
            with av.open(str(video)) as m:
                samples=sum(f.samples for f in m.decode(audio=0));assert samples>0
            save(out/'sheet-source.json',snapshot)
            save(out/'scene-preparation.json',{'sourceVideo':str(source),'sourceMetadata':str(source.parent),'cutoffSeconds':cutoff,'removedText':ENDING,'voice':'3.3','synthesisUsed':False})
            save(out/'video-check.json',{'frames':frames,'seconds':frames/30,'audioSamples':samples,'width':1920,'height':1080})
            assert (await read())['values'][0]==row,'Sheet changed; result remains local'
            updated=[row[0].strip()[:-len(ENDING)].rstrip(),*row[1:9],str(video)]
            for cell,value in [('A8',updated[0]),('J8',updated[9])]:
                result=await c.call_tool('update_cells',{'spreadsheet_id':SID,'range_a1':f"'Видео'!{cell}",'values_json':json.dumps([[value]]),'value_input_option':'RAW'})
                assert not result.isError
            assert (await read())['values'][0]==updated
            print(json.dumps({'video':str(video),'seconds':frames/30,'cutoff':cutoff,'sheetVerified':True}),flush=True)

asyncio.run(main())
