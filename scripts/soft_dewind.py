"""Conservative low-frequency cleanup; preserve originals and sample timing."""
import argparse, hashlib, json, subprocess, time
from pathlib import Path
import imageio_ffmpeg
import numpy as np
import soundfile as sf
import av

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('--video', type=Path)
args = parser.parse_args()
source = args.source.resolve()
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
out = source.parent / f'soft-dewind-{time.time_ns()}'
out.mkdir()
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
def run(arguments):
    subprocess.run([ffmpeg, '-nostdin', '-n', '-hide_banner', '-loglevel', 'error', *arguments], check=True)
original = out / 'original.wav'
cleaned = out / 'cleaned.wav'
run(['-i', str(source), '-c:a', 'pcm_f32le', str(original)])
# Only a 70 Hz, 12 dB/octave high-pass: no spectral denoising, gate, pitch or tempo change.
run(['-i', str(original), '-af', 'highpass=f=70:p=2', '-c:a', 'pcm_f32le', str(cleaned)])
a, rate = sf.read(original, always_2d=True)
b, rate_b = sf.read(cleaned, always_2d=True)
assert rate == rate_b and a.shape == b.shape
assert np.isfinite(b).all() and np.isfinite(a).all()
# Filtering or MP3 decoding can produce peaks above full scale. Apply the same
# constant attenuation to both comparison files, never a limiter/compressor.
peak_before = float(max(np.max(np.abs(a)), np.max(np.abs(b))))
gain = min(1.0, 0.95 / max(peak_before, 1e-20))
a *= gain
b *= gain
sf.write(original, a, rate, subtype='PCM_24')
sf.write(cleaned, b, rate, subtype='PCM_24')
assert np.max(np.abs(b)) < 1
def rms(x): return float(np.sqrt(np.mean(x*x)))
def low_power(x):
    signal = x.mean(axis=1)
    spectrum = np.fft.rfft(signal)
    frequencies = np.fft.rfftfreq(len(signal), 1/rate)
    return float(np.sum(np.abs(spectrum[frequencies < 70])**2))
report = {'source':str(source), 'sourceSha256':source_hash,
          'filter':'highpass=f=70:p=2', 'sampleRate':rate, 'sampleCount':len(a),
          'durationSeconds':len(a)/rate,
          'rmsChangeDb':20*np.log10(rms(b)/rms(a)),
          'below70HzPowerChangeDb':10*np.log10(max(low_power(b),1e-20)/max(low_power(a),1e-20)),
          'sampleCountUnchanged':True, 'clipping':False,
          'comparisonGainDb':20*np.log10(gain), 'peakBeforeAttenuation':peak_before,
          'original':str(original), 'cleaned':str(cleaned)}
if args.video:
    video_hash = hashlib.sha256(args.video.read_bytes()).hexdigest()
    with av.open(str(args.video)) as container:
        video_duration = float(container.streams.video[0].duration * container.streams.video[0].time_base)
    video_out = out / 'scene-with-pointer-cleaned.mp4'
    run(['-i', str(args.video), '-i', str(cleaned), '-map','0:v:0','-map','1:a:0',
         '-c:v','copy','-c:a','aac','-b:a','192k','-af','apad','-t',str(video_duration),
         '-movflags','+faststart',str(video_out)])
    assert hashlib.sha256(args.video.read_bytes()).hexdigest() == video_hash
    report['video'] = str(video_out)
    report['videoStreamCopied'] = True
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
(out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
