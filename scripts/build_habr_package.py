"""Package the authored article with four existing scene captures and an HTML preview."""
import json,shutil,subprocess,html
from pathlib import Path
import av,imageio_ffmpeg,markdown
from material_paths import material_dir
out=material_dir()/'habr-graph-code-2026-09-25';images=out/'images';images.mkdir(exist_ok=True)
base=material_dir()
sources=[
 ('01-swap.png',base/'scene-row015-reuse-1790312716562850400/scene.mp4',18),
 ('02-trace.png',base/'scene-row014-1790082672813904600/2026-09-22 17-14-02.mp4',3),
 ('03-etl.png',base/'scene-row017-1790309045615508700/stage-7.png',None),
 ('04-annotations.png',base/'scene-row020-1790144160395181100/scene.mp4',-1),
]
records=[]
for name,source,t in sources:
    assert source.is_file(),source
    target=images/name
    if t is None:shutil.copy2(source,target)
    else:
        if t<0:
            with av.open(str(source)) as c:t=c.duration/1e6+t
        if not target.exists():subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-v','error','-ss',str(t),'-i',str(source),'-frames:v','1','-update','1',str(target)],check=True)
    records.append({'image':name,'source':str(source),'seconds':t})
(out/'image-sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
text=(out/'article.md').read_text(encoding='utf8')
rendered=markdown.markdown(text,extensions=['tables','fenced_code'])
import re
rendered=re.sub(r'<spoiler title="([^"]+)">',r'<details open><summary>\1</summary>',rendered).replace('</spoiler>','</details>')
page='<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Граф кода как общая память</title><style>body{max-width:850px;margin:48px auto;padding:0 24px;font:18px/1.65 system-ui,sans-serif;color:#263238;background:#fff}h1{font-size:36px;line-height:1.2}h2{margin-top:2em;line-height:1.3}h3{margin-top:1.8em}img{max-width:100%;height:auto;border:1px solid #ddd}pre{overflow:auto;padding:18px;background:#f4f6f7;font-size:14px;line-height:1.5}code{font-family:Consolas,monospace}table{border-collapse:collapse;width:100%;font-size:16px}td,th{border:1px solid #ddd;padding:9px;text-align:left}a{color:#1769aa}summary{cursor:pointer;font-weight:600}details{padding:16px;border:1px solid #ddd}em{color:#52626b}</style><article>'+rendered+'</article></html>'
page=page.replace('</style>','body{overflow-wrap:anywhere}table{display:block;overflow-x:auto}pre{max-width:100%;box-sizing:border-box}@media(max-width:600px){body{margin:24px auto;padding:0 16px;font-size:17px}h1{font-size:28px}td,th{padding:6px}} </style>')
(out/'preview.html').write_text(page,encoding='utf8')
assert text.count('](images/')==4
print(json.dumps({'article':str(out/'article.md'),'preview':str(out/'preview.html'),'images':len(records),'words':len(text.split())},ensure_ascii=False))
