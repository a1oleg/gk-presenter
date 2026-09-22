from material_paths import material_dir
"""Local CPU transcript draft with timestamps; no source audio is uploaded."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--start', type=float, required=True)
    p.add_argument('--seconds', type=float, required=True)
    p.add_argument('--model', default='small')
    p.add_argument('--audio-file', type=Path)
    args = p.parse_args()
    if args.start < 0 or not 0 < args.seconds <= 120:
        p.error('start >= 0; seconds in (0,120]')
    cfg = json.loads((ROOT / 'sources.local.json').read_text(encoding='utf-8'))
    source = str(args.audio_file.resolve()) if args.audio_file else cfg['audioPath']
    out = material_dir('output') / f'transcript-{time.time_ns()}'
    out.mkdir(parents=True)
    import imageio_ffmpeg
    clip = out / 'source.wav'
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-n', '-hide_banner', '-loglevel', 'error',
                    '-ss', str(args.start), '-i', source, '-t', str(args.seconds),
                    '-vn', '-ac', '1', '-ar', '16000', str(clip)], check=True)
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HOME'] = str(ROOT / '.cache' / 'huggingface')
    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device='cpu', compute_type='int8', cpu_threads=8,
                         download_root=str(ROOT / 'models' / 'whisper'))
    start = time.perf_counter()
    segments, info = model.transcribe(str(clip), language='ru', beam_size=5, word_timestamps=True)
    rows = [{'start': s.start, 'end': s.end, 'text': s.text,
             'words': [{'start': w.start, 'end': w.end, 'word': w.word, 'probability': w.probability}
                       for w in (s.words or [])]} for s in segments]
    report = {'sourceAudioPath': source, 'sourceStartSeconds': args.start,
              'durationSeconds': args.seconds, 'model': args.model, 'status': 'machine transcript; review required',
              'transcriptionSeconds': time.perf_counter() - start, 'segments': rows}
    (out / 'transcript.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'transcript.txt').write_text(' '.join(s['text'].strip() for s in rows), encoding='utf-8')
    print(json.dumps({'output': str(out), **report}, ensure_ascii=True, indent=2))

if __name__ == '__main__':
    main()
