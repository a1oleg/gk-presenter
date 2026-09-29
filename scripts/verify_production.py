"""Integration smoke: generic audio/image rendering and meaningful failure checks.

Writes synthetic test materials under the configured material output; no TTS.
Run with .venv/Scripts/python.exe -X utf8 scripts/verify_production.py.
"""
import copy, hashlib, json, math, os, struct, subprocess, sys, tempfile, wave
from pathlib import Path
from PIL import Image, ImageDraw
from material_paths import material_dir
from render_production import prepare, verify_assets

root=Path(__file__).resolve().parents[1]
out=Path(tempfile.mkdtemp(prefix='production-verification-',dir=material_dir()))
image=Image.new('RGB',(240,120),'#214962')
ImageDraw.Draw(image).rectangle((10,10,80,100),fill='#427D99')
image.save(out/'background.png')
with wave.open(str(out/'tone.wav'),'wb') as audio:
    audio.setparams((1,2,24000,0,'NONE','not compressed'))
    audio.writeframes(b''.join(struct.pack('<h',int(1000*math.sin(2*math.pi*220*i/24000))) for i in range(24000)))
text='Проверка якоря'
(out/'alignment.json').write_text(json.dumps({'characters':list(text),'character_start_times_seconds':[i*.04 for i in range(len(text))]},ensure_ascii=False),encoding='utf8')
lesson=json.loads((root/'examples/production/consensus.json').read_text(encoding='utf8'))
lesson['title']='Проверка: изображение и тестовый тон, не речь'
scene=lesson['segments'][0]
lesson['segments']=[scene]
scene['narration']=text
scene['render'].update(background={'kind':'image','file':'background.png'},audio={'mode':'file','file':'tone.wav','alignment':'alignment.json'},tailSeconds=.2)
scene['render'].pop('durationSeconds')
scene['render']['overlays'][0]['text']='Проверка'
scene['render']['overlays'][1]['text']='Тестовый тон, не озвучка'
scene['render']['overlays'][2]['start']={'anchor':'якоря'}
source=out/'lesson.json'
source.write_text(json.dumps(lesson,ensure_ascii=False),encoding='utf8')
result=subprocess.run(['node','scripts/produce.mjs','--lesson',str(source)],cwd=root,check=True,capture_output=True,text=True,encoding='utf8',env={**os.environ,'PYTHONUTF8':'1'})
report=json.loads(result.stdout.strip().splitlines()[-1])
assert report['title']==lesson['title']
assert report['frames']==36
render_dir=Path(report['video']).parent
plan=json.loads((render_dir/'production-plan.json').read_text(encoding='utf8'))
assert plan['scenes'][0]['overlays'][2]['start']==text.index('якоря')*.04
bad=copy.deepcopy(plan);bad['scenes'][0]['overlays'][0]['x']=.99
try:
    prepare(bad)
    raise AssertionError('Clipped text accepted')
except ValueError as error:
    assert 'fit canvas' in str(error)
bad=copy.deepcopy(plan);bad['scenes'][0]['overlays'][0]['start']=20
try:
    prepare(bad)
    raise AssertionError('Out of range timing accepted')
except ValueError as error:
    assert 'outside scene' in str(error)
bad=copy.deepcopy(plan);bad['assets'][0]['sha256']='0'*64
try:
    verify_assets(bad)
    raise AssertionError('Changed asset accepted')
except ValueError as error:
    assert 'Source changed' in str(error)
print(json.dumps({'ok':True,'video':report['video'],'frames':report['frames'],'checks':['unicode','image','audio duration','speech-anchor timing with synthetic alignment','text bounds','timing bounds','source hash']},ensure_ascii=True))
