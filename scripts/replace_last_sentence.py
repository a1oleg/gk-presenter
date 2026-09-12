"""Replace a generated last sentence using recorded boundaries; preserve previous outputs."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
import soundfile as sf

p = argparse.ArgumentParser()
p.add_argument('original_report', type=Path)
p.add_argument('replacement_report', type=Path)
a = p.parse_args()
original = json.loads(a.original_report.read_text(encoding='utf-8'))
replacement = json.loads(a.replacement_report.read_text(encoding='utf-8'))
start = original['sentences'][-1]['start']
old, rate = sf.read(original['audioPath'])
new, new_rate = sf.read(replacement['audioPath'])
if rate != new_rate or old.ndim != 1 or new.ndim != 1:
    raise ValueError('Matching mono sample rates required')
out = Path(__file__).resolve().parents[1] / 'output' / f'sentence-replacement-{time.time_ns()}'
out.mkdir(parents=True)
audio = out / 'synthesized.wav'
sf.write(audio, np.concatenate([old[:round(start*rate)], new]), rate, subtype='PCM_24')
report = {'audioPath': str(audio), 'originalReport': str(a.original_report.resolve()),
          'replacementReport': str(a.replacement_report.resolve()), 'replacementStartSeconds': start,
          'text': '\n'.join([s['text'] for s in original['sentences'][:-1]]+[replacement['text']]),
          'durationSeconds': sf.info(audio).duration, 'licenseScope': 'non-commercial XTTS test'}
(out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=True))
