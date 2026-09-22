from material_paths import material_dir
"""Replace a short clip's speech with a local synthesized WAV, preserving picture timing."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import imageio_ffmpeg
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--synthesized', type=Path, required=True)
    p.add_argument('--start', type=float, required=True)
    p.add_argument('--seconds', type=float, required=True)
    p.add_argument('--speech-start', type=float, default=0)
    p.add_argument('--speech-end', type=float)
    p.add_argument('--pitch', type=float, help='Override saved pitch; zero bypasses pitch processing')
    p.add_argument('--natural-timing', action='store_true', help='Never time-stretch; pad audio or extend video clip interval')
    args = p.parse_args()
    source_seconds = args.seconds
    cfg = json.loads((ROOT / 'sources.local.json').read_text(encoding='utf-8'))
    speech_end = args.speech_end if args.speech_end is not None else args.seconds
    if not (0 <= args.start and 0 <= args.speech_start < speech_end <= args.seconds <= 120):
        p.error('Invalid clip or speech interval')
    if not cfg.get('voiceConsent') or not cfg.get('xttsLicense', {}).get('accepted'):
        raise RuntimeError('Owner consent and non-commercial test license required')
    pitch = args.pitch if args.pitch is not None else cfg.get('preferredVoicePostProcessing', {}).get('pitchSemitones', -1)
    if not -12 <= pitch <= 12:
        p.error('pitch must be within [-12,12]')
    info = sf.info(args.synthesized)
    if args.natural_timing:
        speech_end = args.speech_start + info.duration
        args.seconds = max(args.seconds, speech_end + 0.3)
    tempo = 1 if args.natural_timing else info.duration / (speech_end - args.speech_start)
    if not 0.75 <= tempo <= 1.3:
        raise RuntimeError(f'Timing needs excessive stretch ({tempo:.3f}); adjust text or clip, not picture speed')
    out = material_dir('output') / f'revoice-{time.time_ns()}'
    out.mkdir(parents=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    def run(options):
        subprocess.run([ffmpeg, '-nostdin', '-n', '-hide_banner', '-loglevel', 'error', *options], check=True)
    processed = out / 'voice.wav'
    transform = (f'rubberband=tempo={tempo}:pitch={2 ** (pitch/12)}:formant=preserved:pitchq=quality,'
                 if pitch != 0 or tempo != 1 else '')
    run(['-i', str(args.synthesized), '-af', transform +
         f'adelay={round(args.speech_start*1000)}:all=1,apad,atrim=duration={args.seconds}',
         '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s24le', str(processed)])
    if abs(sf.info(processed).duration - args.seconds) > 0.01:
        raise RuntimeError('Processed audio duration mismatch')
    original = out / 'original.mp4'
    padding = max(0, args.seconds-source_seconds)
    run(['-ss', str(args.start), '-t', str(source_seconds), '-i', cfg['videoPath'],
         '-ss', str(args.start), '-t', str(source_seconds), '-i', cfg['audioPath'],
         '-map', '0:v:0', '-map', '1:a:0', '-t', str(args.seconds),
         '-vf', f'tpad=stop_mode=clone:stop_duration={padding}', '-af', 'apad',
         '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(original)])
    dubbed = out / f'revoiced-pitch-{pitch:g}.mp4'
    run(['-i', str(original), '-i', str(processed), '-map', '0:v:0', '-map', '1:a:0',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', str(args.seconds),
         '-movflags', '+faststart', str(dubbed)])
    # Decoding checks reveal broken output files without relying on filenames.
    for clip in [original, dubbed]:
        run(['-i', str(clip), '-f', 'null', '-'])
    report = {'original': str(original), 'revoiced': str(dubbed), 'voice': str(processed),
              'sourceStartSeconds': args.start, 'clipSeconds': args.seconds,
              'synthesizedSource': str(args.synthesized.resolve()), 'rawVoiceSeconds': info.duration,
              'pitchSemitones': pitch, 'formants': 'preserved', 'tempoFactor': tempo,
              'speechStart': args.speech_start, 'speechEnd': speech_end,
              'pictureTiming': 'original playback speed; same encoded video stream in both comparison files',
              'sourceVideoSeconds': source_seconds, 'trailingFreezeSeconds': padding,
              'audioPolicy': 'Original audio replaced completely, not mixed; no background preserved',
              'licenseScope': 'non-commercial test only'}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))

if __name__ == '__main__':
    main()
