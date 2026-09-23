import sys as _material_sys
from pathlib import Path as _MaterialPath
_material_sys.path.insert(0,str(_MaterialPath(__file__).resolve().parents[1]/'scripts'))
from material_paths import material_dir
import asyncio, base64, json, re, subprocess, time, urllib.request
from pathlib import Path
import av, imageio_ffmpeg
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path('C:/GitHub/graphKoda-presenter')
SID = '1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'
REPLACEMENTS = {'current': 'ка́рэнт', 'value': 'вэ́лью', 'length': 'лэнгс',
                'undefined': 'андифа́йнд', 'alphabet': 'а́лфабет', 'index': 'и́ндекс'}
def spoken(text):
    return re.sub(r'\b(' + '|'.join(REPLACEMENTS) + r')\b', lambda m: REPLACEMENTS[m[0]], text)
def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')
def duration(path):
    with av.open(str(path)) as c:
        return c.duration / av.time_base

async def main():
    async with stdio_client(StdioServerParameters(command='C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe', args=['C:/GitHub/google-sheets-mcp/server.py'])) as (r,w):
        async with ClientSession(r,w) as c:
            await c.initialize()
            async def read():
                result = await c.call_tool('get_sheet_data_by_notation', {'spreadsheet_id': SID, 'notation': '!A8:J8'})
                assert not result.isError
                return json.loads(result.content[0].text)
            snapshot = await read()
            row = snapshot['values'][0]
            assert row[8] == '3.3' and 'current' in row[0] and 'length' in row[0]
            old_video = Path(row[9])
            assert old_video.is_file() and old_video.parent.name == 'scene-row008-1789992257969326200'
            preparation = json.loads((old_video.parent/'scene-preparation.json').read_text(encoding='utf8'))
            out = material_dir('output')/f'scene-row008-phonetic-{time.time_ns()}'
            out.mkdir()
            print('OUTPUT='+str(out), flush=True)
            save(out/'sheet-source.json', snapshot)
            text = spoken(row[0].strip())
            save(out/'pronunciation.json', {'displayText': row[0], 'spokenText': text, 'replacements': REPLACEMENTS})
            env = dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.lstrip().startswith('#'))
            key = env['ELEVENLABS_API_KEY'].strip().strip('"').strip("'")
            voice = json.loads((material_dir('output') / 'voice-mix-comparison-1789454509647/voice.local.json').read_text())['voice_id']
            payload = {'text': text, 'model_id': 'eleven_v3', 'voice_settings': {'stability': 0.5, 'similarity_boost': 1.0}}
            save(out/'request.json', {'voice_id': voice, **payload})
            req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128', data=json.dumps(payload).encode(), headers={'xi-api-key':key,'Content-Type':'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=90) as res:
                reply = json.load(res)
            (out/'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
            save(out/'alignment.json', reply)
            alignment = reply['alignment']
            aligned_text = ''.join(alignment['characters'])
            points = [(0.0,0.0)]
            events = []
            for event in preparation['events']:
                anchor = spoken(event['anchor'])
                i = aligned_text.find(anchor)
                assert i >= 0, anchor
                new_time = alignment['character_start_times_seconds'][i]
                if event['time'] > 0:
                    points.append((event['time'],new_time))
                events.append({**event, 'originalTime':event['time'], 'time':new_time, 'spokenAnchor':anchor})
            target_duration = duration(out/'speech.mp3') + .3
            points.append((duration(old_video),target_duration))
            filters = []
            for n, ((a,b),(x,y)) in enumerate(zip(points,points[1:])):
                assert x > a and y > b
                filters.append(f'[0:v]trim=start={a}:end={x},setpts={(y-b)/(x-a)}*(PTS-STARTPTS),fps=30,setsar=1[v{n}]')
            filters.append(''.join(f'[v{n}]' for n in range(len(points)-1))+f'concat=n={len(points)-1}:v=1:a=0[v]')
            video = out/'scene.mp4'
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-i',str(old_video),'-i',str(out/'speech.mp3'),'-filter_complex',';'.join(filters),'-map','[v]','-map','1:a','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t',str(target_duration),'-movflags','+faststart',str(video)],check=True)
            with av.open(str(video)) as media:
                size = (media.streams.video[0].width,media.streams.video[0].height)
                assert size == (1920,1080)
                frames = sum(1 for _ in media.decode(video=0))
                assert abs(frames/30-target_duration)<.2
            with av.open(str(video)) as media:
                samples = sum(f.samples for f in media.decode(audio=0))
                assert samples>0
            save(out/'scene-preparation.json', {**preparation,'originalVideo':str(old_video),'events':events,'retimingPoints':points,'visualContentPreserved':True})
            report = {'video':str(video),'seconds':frames/30,'width':1920,'height':1080,'voice':'3.3','audioSamples':samples,'pointerCues':len(events)}
            save(out/'video-check.json',report)
            assert (await read())['values'][0] == row, 'Sheet changed; new video remains local'
            result = await c.call_tool('update_cells', {'spreadsheet_id':SID,'range_a1':"'Видео'!J8",'values_json':json.dumps([[str(video)]]),'value_input_option':'RAW'})
            assert not result.isError
            assert (await read())['values'][0] == [*row[:9],str(video)]
            print(json.dumps({**report,'sheetVerified':True}),flush=True)

asyncio.run(main())
