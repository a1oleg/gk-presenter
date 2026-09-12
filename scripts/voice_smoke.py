"""CPU-only non-commercial XTTS smoke test. Never uploads source audio.

Run --prepare-only first to make a candidate reference, then listen to it.
Output/model caches are local and ignored by Git. Original files are read-only.
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--start', type=float, default=60)
    parser.add_argument('--seconds', type=float, default=12)
    parser.add_argument('--threads', type=int, default=8)
    parser.add_argument('--text-file', type=Path, default=ROOT / 'examples' / 'voice-test.txt')
    parser.add_argument('--audio-file', type=Path, help='Alternative local recording of the consenting owner')
    parser.add_argument('--by-line', action='store_true', help='Synthesize short lines independently with inspectable boundaries')
    args = parser.parse_args()
    if args.start < 0 or not 3 <= args.seconds <= 30 or args.threads < 1:
        parser.error('start >= 0, seconds in [3,30], threads >= 1 required')
    config = json.loads((ROOT / 'sources.local.json').read_text(encoding='utf-8'))
    if config.get('voiceConsent') is not True:
        raise RuntimeError('Explicit owner voice consent required')
    source_audio = args.audio_file.resolve() if args.audio_file else Path(config['audioPath'])
    if not source_audio.is_file():
        raise FileNotFoundError(source_audio)
    output = ROOT / 'output' / f'voice-test-{time.time_ns()}'
    output.mkdir(parents=True)
    reference = output / 'reference.wav'
    import imageio_ffmpeg
    subprocess.run([
        imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-n', '-hide_banner', '-loglevel', 'error',
        '-ss', str(args.start), '-i', str(source_audio), '-t', str(args.seconds),
        '-vn', '-ac', '1', '-ar', '24000', '-c:a', 'pcm_s16le', str(reference),
    ], check=True)
    import soundfile as sf
    ref_info = sf.info(reference)
    if ref_info.duration < 3:
        raise RuntimeError('Reference too short; check source and offset')
    report = {
        'sourceAudioPath': str(source_audio),
        'sourceStartSeconds': args.start, 'referenceDurationSeconds': ref_info.duration,
        'reference': str(reference), 'licenseScope': 'non-commercial test only',
        'referenceQuality': 'candidate; not manually approved',
        'device': 'cpu', 'threads': args.threads,
        'packages': {name: importlib.metadata.version(name)
                     for name in ['coqui-tts', 'torch', 'torchaudio', 'transformers', 'soundfile', 'imageio-ffmpeg']},
    }
    print(json.dumps(report, ensure_ascii=True), flush=True)
    if not args.prepare_only:
        if config.get('xttsLicense', {}).get('accepted') is not True:
            raise RuntimeError('CPML acceptance required before downloading XTTS weights')
        os.environ['TTS_HOME'] = str(ROOT / 'models')
        os.environ['HF_HOME'] = str(ROOT / '.cache' / 'huggingface')
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.environ['COQUI_TOS_AGREED'] = '1'  # Explicit acceptance in local config.
        import torch
        torch.set_num_threads(args.threads)
        from TTS.api import TTS
        started = time.perf_counter()
        engine = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to('cpu')
        report['loadSeconds'] = time.perf_counter() - started
        text = args.text_file.read_text(encoding='utf-8').strip()
        if not text:
            raise ValueError('Empty test text')
        destination = output / 'synthesized.wav'
        started = time.perf_counter()
        if args.by_line:
            import numpy as np
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if any(len(line) > 180 for line in lines):
                raise ValueError('Split long lines at a natural sentence boundary (max 180 characters)')
            combined, boundaries = [], []
            cursor = 0
            for index, line in enumerate(lines):
                part = output / f'sentence-{index+1:02d}.wav'
                engine.tts_to_file(text=line, speaker_wav=str(reference), language='ru',
                                  file_path=str(part), split_sentences=False)
                samples, rate = sf.read(part)
                if rate != 24000 or samples.ndim != 1:
                    raise ValueError('Unexpected XTTS audio format')
                # Short boundary fades prevent splice clicks, not model voice artifacts.
                fade = min(round(rate * 0.01), len(samples) // 2)
                if fade:
                    samples[:fade] *= np.linspace(0, 1, fade)
                    samples[-fade:] *= np.linspace(1, 0, fade)
                boundaries.append({'text': line, 'start': cursor/rate,
                                   'end': (cursor+len(samples))/rate, 'rawAudio': str(part)})
                combined.append(samples)
                cursor += len(samples)
                if index < len(lines)-1:
                    silence = np.zeros(round(rate * 0.25))
                    combined.append(silence)
                    cursor += len(silence)
            sf.write(destination, np.concatenate(combined), 24000, subtype='PCM_24')
            report['sentences'] = boundaries
        else:
            engine.tts_to_file(text=text, speaker_wav=str(reference), language='ru',
                               file_path=str(destination), split_sentences=True)
        report['synthesisSeconds'] = time.perf_counter() - started
        report['audioDurationSeconds'] = sf.info(destination).duration
        report['realTimeFactor'] = report['synthesisSeconds'] / report['audioDurationSeconds']
        report['audioPath'] = str(destination)
        report['text'] = text
        print(json.dumps(report, ensure_ascii=True, indent=2), flush=True)
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
