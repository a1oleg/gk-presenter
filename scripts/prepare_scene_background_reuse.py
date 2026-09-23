"""Combine an approved preview with an existing narration, without synthesis."""
import json,shutil,sys,time
from pathlib import Path
from material_paths import material_dir
old,preview=map(Path,sys.argv[1:3]);row=int(sys.argv[3])
out=material_dir()/f'scene-row{row:03d}-background-{time.time_ns()}';out.mkdir()
for name in ['request.json','alignment.json','sheet-source.json','speech.mp3']:
 shutil.copy2(old/name,out/name)
for name in ['source.drawio','scene.png','screen-geometry.json','validate_geometry.json','assets.json']:
 if (preview/name).exists():shutil.copy2(preview/name,out/name)
(out/'audio-source.json').write_text(json.dumps({'video':str(old/'scene.mp4'),'audioUnchanged':True}),encoding='utf8')
print(out)
