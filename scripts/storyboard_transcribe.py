from material_paths import material_dir
"""Resumable local full-video transcription in bounded chunks; no cloud upload."""
import json
import os
from pathlib import Path
import subprocess
import time
import av
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
source = Path(json.loads((ROOT / 'sources.local.json').read_text(encoding='utf-8'))['videoPath'])
out = material_dir('output') / 'storyboard-coldKode2'
out.mkdir(exist_ok=True)
with av.open(str(source)) as media:
    duration = media.duration / 1_000_000
signature = {'path': str(source), 'bytes': source.stat().st_size, 'mtime': source.stat().st_mtime_ns}
manifest = out / 'source.json'
if manifest.exists() and json.loads(manifest.read_text()) != signature:
    raise RuntimeError('Source changed; use a different output directory')
manifest.write_text(json.dumps(signature), encoding='utf-8')
os.environ['HF_HOME'] = str(ROOT / '.cache/huggingface')
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=8,
                     download_root=str(ROOT / 'models/whisper'))
for index, start in enumerate(range(0, int(duration) + 1, 240)):
    report_path = out / f'chunk-{index:02d}.json'
    if report_path.exists():
        print(f'Cached chunk {index}', flush=True)
        continue
    seconds = min(240, duration-start)
    wav = out / f'chunk-{index:02d}.wav'
    if not wav.exists():
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-n', '-hide_banner', '-loglevel', 'error',
                        '-ss', str(start), '-i', str(source), '-t', str(seconds), '-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)
    began = time.perf_counter()
    segments, _ = model.transcribe(str(wav), language='ru', beam_size=5, word_timestamps=True,
        initial_prompt='Техническая презентация: Claude Code, coldKode, TypeScript, React, Neo4j, draw.io, VS Code, Codex, onSubmit, helpers, аннотатор, экстрактор, граф кода.')
    rows = [{'start': round(start+s.start,3), 'end': round(start+s.end,3), 'text': s.text.strip(),
             'words': [{'start':round(start+w.start,3), 'end':round(start+w.end,3), 'word':w.word, 'probability':w.probability} for w in s.words or []]} for s in segments]
    report_path.write_text(json.dumps({'start':start,'end':start+seconds,'segments':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Completed {index}: {start:.0f}-{start+seconds:.0f}s in {time.perf_counter()-began:.1f}s',flush=True)
chunks = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(out.glob('chunk-*.json'))]
(out/'transcript.json').write_text(json.dumps({'duration':duration,'segments':[s for c in chunks for s in c['segments']]},ensure_ascii=False,indent=2),encoding='utf-8')
print('Complete',flush=True)
