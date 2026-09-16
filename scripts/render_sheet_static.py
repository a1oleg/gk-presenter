"""Render a static sheet scene from a local image or a Google Slides page URL.

Run with google-sheets-mcp's Python; media encoding uses presenter Python.
"""
import argparse,json,subprocess,hashlib
from pathlib import Path
from fetch_google_slide import fetch_slide,parse_slide_url
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();out=a.output.resolve()
root=Path(__file__).resolve().parents[1]
snapshot=json.loads((out/'sheet-source.json').read_text(encoding='utf8'));row=snapshot['values'][1]
assert row[2:4]==['нет','нет'],'Static rendering requires cursor=no and interactive=no'
source=row[1].strip().strip('"')
if source.startswith('https://'):
 parse_slide_url(source)
 cached=out/'google-slide.json'
 if cached.exists():
  report=json.loads(cached.read_text(encoding='utf8'));assert report['sourceUrl']==source
  assert hashlib.sha256(Path(report['image']).read_bytes()).hexdigest()==report['sha256']
 else:report=fetch_slide(source,out)
 background=Path(report['image'])
else:background=Path(source)
assert background.is_file()
subprocess.run([str(root/'.venv/Scripts/python.exe'),str(root/'scripts/render_static_scene.py'),str(out),'--background',str(background),'--canvas','1600x900'],check=True)
