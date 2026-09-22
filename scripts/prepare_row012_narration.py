"""Read the current scene through MCP and synthesize once without editing Sheets."""
import asyncio
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import dotenv_values
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from material_paths import material_dir

ROOT = Path(__file__).resolve().parents[1]
SHEETS = ROOT.parent / 'google-sheets-mcp'
SID = '1otWSZpQP7BueI3vrWpc5M4qOgPxgBbpGEIW8yMEvjSw'


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


async def main():
    params = StdioServerParameters(command=str(SHEETS / '.venv/Scripts/python.exe'), args=[str(SHEETS / 'server.py')])
    snapshots = {}
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            for name, notation in [('headers', '!A1:Z1'), ('scene', '!A12:L12')]:
                result = await client.call_tool('get_sheet_data_by_notation', {'spreadsheet_id': SID, 'notation': notation})
                if result.isError:
                    raise RuntimeError(str(result.content))
                snapshots[name] = json.loads(result.content[0].text)
    row = snapshots['scene']['values'][0]
    if row[11] != '3.3':
        raise RuntimeError('Voice selection changed; resolve it before synthesis')
    reference = material_dir() / 'scene-row011-captions-1790056098495880100/request.json'
    previous_request = json.loads(reference.read_text(encoding='utf-8'))
    if previous_request['model_id'] != 'eleven_v3':
        raise RuntimeError('Voice reference model mismatch')
    key = dotenv_values(ROOT / '.env')['ELEVENLABS_API_KEY']
    voice = previous_request['voice_id']
    check = urllib.request.Request(f'https://api.elevenlabs.io/v1/voices/{voice}', headers={'xi-api-key': key})
    with urllib.request.urlopen(check, timeout=30) as response:
        json.load(response)
    out = material_dir() / f'scene-row012-{time.time_ns()}'
    out.mkdir()
    save(out / 'sheet-source.json', snapshots)
    payload = {'text': row[0].strip(), 'model_id': 'eleven_v3', 'voice_settings': {'stability': 0.5, 'similarity_boost': 1.0}}
    save(out / 'request.json', {'voice_id': voice, **payload})
    print('OUTPUT=' + str(out), flush=True)
    request = urllib.request.Request(
        f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',
        data=json.dumps(payload).encode(), headers={'xi-api-key': key, 'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            reply = json.load(response)
            cost = response.headers.get('character-cost')
    except urllib.error.HTTPError as error:
        save(out / 'failure.json', {'status': error.code, 'retry': False})
        raise RuntimeError(f'TTS HTTP {error.code}; no automatic retry') from None
    (out / 'speech.mp3').write_bytes(base64.b64decode(reply.pop('audio_base64')))
    save(out / 'alignment.json', reply)
    alignment = reply.get('normalized_alignment') or reply['alignment']
    report = {'audio': str(out / 'speech.mp3'), 'seconds': alignment['character_end_times_seconds'][-1], 'characters': len(payload['text']), 'characterCost': cost, 'voice': '3.3', 'sheetModified': False}
    save(out / 'report.json', report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main())
