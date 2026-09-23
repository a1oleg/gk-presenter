"""Render aligned flow/sequence endpoints with a speech-timed crossfade."""
import json, shutil, subprocess, sys, unicodedata
from pathlib import Path
import av
import imageio_ffmpeg

out, endpoints = map(Path, sys.argv[1:3])
data = json.loads((out/'alignment.json').read_text(encoding='utf8'))
a = data.get('normalized_alignment') or data['alignment']
letters, positions = [], []
for i, ch in enumerate(a['characters']):
    for c in unicodedata.normalize('NFD', ch.casefold()):
        if unicodedata.category(c) != 'Mn':
            letters.append(c); positions.append(i)
text = ''.join(letters)
def onset(phrase):
    assert text.count(phrase) == 1, f'Ambiguous/missing cue: {phrase}'
    return a['character_start_times_seconds'][positions[text.index(phrase)]]
start, end = onset('сиквенс'), onset('ну почти')
with av.open(str(out/'speech.mp3')) as media:
    duration = sum(frame.samples/frame.sample_rate for frame in media.decode(audio=0))
assert 0 < start < end < duration
for name in ['flow.png','sequence.png','alignment-check.json']:
    shutil.copy2(endpoints/name,out/name)
scenario=json.loads((endpoints/'scenario.json').read_text(encoding='utf8'))
scenario.update(duration=duration, voice='3.3', transition={
    'kind':'fade','start':start,'end':end,'duration':end-start,
    'startCue':'сиквенс','endCue':'ну почти','timingSource':'ElevenLabs character alignment'})
(out/'scenario.json').write_text(json.dumps(scenario,ensure_ascii=False,indent=2),encoding='utf8')
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-n']
for name in ['flow.png','sequence.png']:
    cmd += ['-loop','1','-framerate','30','-i',str(out/name)]
cmd += ['-i',str(out/'speech.mp3'),'-filter_complex',
        f'[0:v][1:v]xfade=transition=fade:duration={end-start:.6f}:offset={start:.6f},format=yuv420p[v]',
        '-map','[v]','-map','2:a','-t',str(duration),'-c:v','libx264','-crf','18',
        '-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'scene.mp4')]
subprocess.run(cmd,check=True)
print(json.dumps({'duration':duration,'transition':scenario['transition'],'video':str(out/'scene.mp4')},ensure_ascii=False))
