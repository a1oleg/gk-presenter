"""Place scene narration over a Camtasia recording without changing its timing."""
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
import av
import imageio_ffmpeg

out = Path(sys.argv[1]).resolve()
rendered = out / 'scene-compatible.mp4'
snapshot = json.loads((out / 'sheet-source.json').read_text(encoding='utf-8'))
row = snapshot['values'][0]
source = Path(row[2].strip().strip('"'))
assert source.is_file() and source.suffix.lower() in ('.trec', '.mp4')
with av.open(str(source)) as media:
    video = media.streams.video[0]
    width, height = video.width, video.height
    source_duration = media.duration / 1_000_000
assert width <= 1920 and height <= 1080, 'Source must fit without scaling'
with av.open(str(out / 'speech.mp3')) as speech:
    speech_duration = speech.duration / 1_000_000
duration = math.ceil(max(source_duration, speech_duration) * 30) / 30
hold = max(0, duration - source_duration)
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-n', '-v', 'error',
    '-i', str(source), '-i', str(out / 'speech.mp3'), '-map', '0:v:0', '-map', '1:a:0',
    # TREC may stop emitting unchanged screen frames before container duration.
    # Pad generously; the explicit output duration below is authoritative.
    '-vf', f'fps=30,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,tpad=stop_mode=clone:stop_duration={duration}',
    '-af', 'apad', '-t', str(duration), '-c:v', 'libx264', '-crf', '16', '-preset', 'slow',
    '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level:v', '4.1',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(rendered)], check=True)
with av.open(str(rendered)) as media:
    codec = media.streams.video[0].codec_context
    assert codec.name == 'h264' and codec.pix_fmt == 'yuv420p' and codec.profile == 'High'
    frames = sum(1 for frame in media.decode(video=0))
assert abs(frames / 30 - duration) < .04
with av.open(str(rendered)) as media:
    samples = sum(frame.samples for frame in media.decode(audio=0))
assert samples > 0
rendered.replace(out / 'scene.mp4')
scenario = {'kind': 'camtasia-narration', 'duration': duration, 'source': str(source),
    'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'sourceSize': [width, height], 'outputSize': [1920, 1080], 'scale': 1,
    'narrationStart': 0, 'originalAudio': 'replaced', 'voice': row[15],
    'timing': 'source speed preserved; last frame held through narration',
    'sourceDuration': source_duration, 'lastFrameHold': hold, 'frames': frames}
(out / 'scenario.json').write_text(json.dumps(scenario, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(scenario, ensure_ascii=False))
