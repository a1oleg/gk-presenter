from material_paths import material_dir
"""Make mild pitch comparisons with preserved tempo and formants; never overwrite."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import imageio_ffmpeg
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--semitones', type=float, nargs='+', default=[-0.5, -1])
    args = parser.parse_args()
    source = args.source.resolve()
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    samples, rate = sf.read(source, always_2d=True)
    output = material_dir('output') / f'pitch-compare-{time.time_ns()}'
    output.mkdir(parents=True)
    report = {'source': str(source), 'sourceSha256': original_hash,
              'formants': 'preserved', 'tempo': 1, 'licenseScope': 'non-commercial XTTS test', 'variants': []}
    # Equal RMS prevents simple loudness differences from biasing comparison.
    target_rms = float(np.sqrt(np.mean(samples ** 2)))
    variants = []
    if any(not np.isfinite(s) or not -12 <= s <= 12 for s in args.semitones):
        parser.error('semitones must be finite and within [-12, 12]')
    requested = list(dict.fromkeys([0, *args.semitones]))
    for semitones in requested:
        label = 'original' if semitones == 0 else f'{"minus" if semitones < 0 else "plus"}-{abs(semitones):g}'
        if semitones == 0:
            processed = samples.copy()
        else:
            raw = output / f'{label}-processing.wav'
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-n', '-hide_banner',
                            '-loglevel', 'error', '-i', str(source), '-af',
                            f'rubberband=tempo=1:pitch={2 ** (semitones / 12)}:formant=preserved:pitchq=quality',
                            '-c:a', 'pcm_f32le', str(raw)], check=True)
            processed, processed_rate = sf.read(raw, always_2d=True)
            if processed_rate != rate or abs(len(processed) - len(samples)) > rate * 0.05:
                raise RuntimeError('Unexpected rate or duration change')
            processed = processed[:len(samples)]
            if len(processed) < len(samples):
                processed = np.pad(processed, ((0, len(samples) - len(processed)), (0, 0)))
        rms = float(np.sqrt(np.mean(processed ** 2)))
        if rms:
            processed *= target_rms / rms
        variants.append((semitones, label, processed))
    # One shared headroom adjustment, not different peak-normalization per variant.
    peak = max(float(np.max(np.abs(v))) for _, _, v in variants)
    gain = min(1.0, 0.95 / peak) if peak else 1.0
    for semitones, label, processed in variants:
        destination = output / f'{label}.wav'
        sf.write(destination, processed * gain, rate, subtype='PCM_24')
        report['variants'].append({'semitones': semitones, 'path': str(destination),
                                   'durationSeconds': len(processed) / rate})
    report['sharedHeadroomGain'] = gain
    if hashlib.sha256(source.read_bytes()).hexdigest() != original_hash:
        raise RuntimeError('Source changed during processing')
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))

if __name__ == '__main__':
    main()
