"""Mux the successful real capture with narration and validate decoded streams."""
import json
import subprocess
import sys
from pathlib import Path
import av
import imageio_ffmpeg

out = Path(sys.argv[1]).resolve()
recording = json.loads((out / 'recording.json').read_text(encoding='utf-8'))
assert [e['input'].get('index') for e in recording['events'] if e['input']['action'] == 'selectCase'] == [0, 1, 3, 6, 7]
video = out / 'scene-interactive.mp4'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-n',
                '-i', recording['outputPath'], '-i', str(out / 'speech.mp3'),
                '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-af', 'apad', '-t', '25.46', '-movflags', '+faststart', str(video)], check=True)
samples = []
frames = 0
with av.open(str(video)) as container:
    stream = container.streams.video[0]
    assert (stream.width, stream.height) == (1920, 1080)
    assert container.streams.audio
    for frame in container.decode(video=0):
        if frames % 30 == 0:
            small = frame.reformat(width=64, height=36, format='gray')
            pixels = bytes(small.planes[0])
            rows = [pixels[y*small.planes[0].line_size:y*small.planes[0].line_size+64] for y in range(36)]
            values = b''.join(rows)
            mean = sum(values)/len(values)
            variance = sum((x-mean)**2 for x in values)/len(values)
            assert variance > 20, 'Blank or uniform captured frame'
            samples.append({'frame': frames, 'mean': mean, 'variance': variance})
        frames += 1
    assert abs(frames/30-25.46) < 0.15
with av.open(str(video)) as container:
    audio_frames = sum(1 for _ in container.decode(audio=0))
assert audio_frames > 0
report = {'video': str(video), 'frames': frames, 'seconds': frames/30, 'width': 1920, 'height': 1080,
          'audioFrames': audio_frames, 'audioSource': str(out/'speech.mp3'), 'microphoneAudioUsed': False,
          'sessionId': recording['sessionId'], 'pixelChecks': samples,
          'verification': 'Decoded streams, pixel variation, and acknowledged UI actions; no screenshot review'}
(out/'video-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'pixelChecks'}, ensure_ascii=False))
