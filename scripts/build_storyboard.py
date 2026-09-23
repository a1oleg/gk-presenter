from material_paths import material_dir
"""Build reviewed paragraph manifest, video stills and a local review gallery."""
import concurrent.futures
import html
import json
from pathlib import Path
import subprocess
import imageio_ffmpeg
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = material_dir('output') / 'storyboard-graphKoda2'
source = Path(json.loads((OUT/'source.json').read_text())['path'])
snapshot = json.loads((OUT/'sheet-before.json').read_text(encoding='utf-8'))
prefix_times = [(0,5.12),(5.7,9.9),(10.4,22.18),(22.74,40.6),(40.9,54.1),(54.1,63.2),(64,80.3),(81.7,96),(96.6,120.1),(120.68,133.78),(134.24,157.92)]
paragraphs = []
for index, (start,end) in enumerate(prefix_times):
    paragraphs.append({'start':start,'end':end,'text':snapshot['values'][index+1][1], 'preserveExistingText':True})
for path in sorted(OUT.glob('paragraphs-*.json')):
    paragraphs.extend(json.loads(path.read_text(encoding='utf-8')))
frames = OUT / 'frames'
frames.mkdir(exist_ok=True)
for index,p in enumerate(paragraphs):
    assert 0 <= p['start'] < p['end'] <= 2335.765
    assert not index or p['start'] >= paragraphs[index-1]['end'] - 0.01
    p.update(row=index+2, frameSeconds=round((p['start']+p['end'])/2,3), frame=f'frames/row-{index+2:03d}.jpg')
    overrides = {3:5.8,44:936.8,73:1649.0}
    if p['row'] in overrides:
        p.update(frameSeconds=overrides[p['row']],frame=f'frames/row-{p["row"]:03d}-selected.jpg')
def extract(p):
    path = OUT/p['frame']
    if not path.exists():
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-ss',str(p['frameSeconds']),'-i',str(source),'-frames:v','1','-q:v','3',str(path)],check=True)
    with Image.open(path) as image:
        assert image.size == (1920,1080)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(extract,paragraphs))
manifest={'source':str(source),'timingStatus':'Approximate ASR timestamps, lightly edited narration; frame time is the midpoint of each speech interval','paragraphs':paragraphs}
(OUT/'storyboard.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
def stamp(t):
    return f'{int(t)//60:02d}:{int(t)%60:02d}'
cards=[]
for p in paragraphs:
    cards.append(f'<article><h2>Строка {p["row"]}: {stamp(p["start"])}–{stamp(p["end"])}</h2><a href="{p["frame"]}"><img src="{p["frame"]}" loading="lazy"></a><p>{html.escape(p["text"])}</p></article>')
(OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>graphKoda2 — раскадровка</title><style>body{font:18px sans-serif;max-width:1150px;margin:30px auto;background:#eee}article{background:white;padding:20px;margin:20px 0}img{width:100%}p{line-height:1.5}</style>'+''.join(cards),encoding='utf-8')
for batch in range(0,len(paragraphs),12):
    subset=paragraphs[batch:batch+12]
    canvas=Image.new('RGB',(1920,3*300),'white')
    draw=ImageDraw.Draw(canvas)
    for i,p in enumerate(subset):
        with Image.open(OUT/p['frame']) as im:
            im.thumbnail((480,270))
            x,y=(i%4)*480,(i//4)*300
            canvas.paste(im,(x,y+25))
            draw.text((x+5,y+5),f'Row {p["row"]} | {stamp(p["frameSeconds"])}',fill='black')
    canvas.save(OUT/f'review-{batch//12:02d}.jpg',quality=90)
print(f'Built {len(paragraphs)} paragraphs and frames. Originals preserved: {len(prefix_times)}')
