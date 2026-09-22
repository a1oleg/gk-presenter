import json,subprocess,sys
from pathlib import Path
out=Path(sys.argv[1]).resolve()
meta=json.loads((out/'clearance.json').read_text(encoding='utf8'))
if not (out/'scene-preparation.json').exists():
 (out/'scene-preparation.json').write_text(json.dumps({'recording':meta['recording']},indent=2),encoding='utf8')
subprocess.run(['node',str(Path(__file__).resolve().parent/'render_motion_captions.mjs'),str(out),'--preview','4.666667','--filename','preview.png'],check=True)
print(out/'preview.png')
