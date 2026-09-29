"""Render diagram and semantic code as independent video tracks, then compose.

Inputs are a clean diagram export and code-source.json, never a VS Code screenshot.
The manifest supplies layout, timing, source geometry and optional prepared audio.
"""
import argparse, hashlib, json, math, subprocess, tempfile
from pathlib import Path
import av
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageOps
from material_paths import material_dir


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def fit_code(snapshot, size, font_file, minimum=18, maximum=30, padding=28):
    lines=snapshot['code'].split('\n')
    if len(lines)!=len(snapshot['lineMap']):
        raise ValueError('Code line map differs from source')
    if len(snapshot['colors'])!=len(snapshot['code'].encode('utf-16-le'))//2:
        raise ValueError('Semantic color map differs from source')
    if any('\t' in line for line in lines):
        raise ValueError('Expand tabs in the semantic snapshot before rendering')
    for font_size in range(maximum,minimum-1,-1):
        font=ImageFont.truetype(font_file,font_size)
        line_height=math.ceil(font_size*1.55)
        gutter=math.ceil(font.getlength(str(max(snapshot['lineMap']))))+20
        widest=max(font.getlength(line) for line in lines)
        if padding*2+gutter+widest <= size[0] and padding*2+len(lines)*line_height <= size[1]:
            return dict(font=font,fontSize=font_size,lineHeight=line_height,gutter=gutter,padding=padding,lines=lines)
    raise ValueError('Code does not fit without clipping or unreadable text; enlarge code track or select fewer source lines')


def code_frame(snapshot,layout,size,event=None):
    image=Image.new('RGB',size,'#1e1e1e');draw=ImageDraw.Draw(image)
    font=layout['font'];pad=layout['padding'];x0=pad+layout['gutter'];offset=0
    for i,line in enumerate(layout['lines']):
        y=pad+i*layout['lineHeight']
        if event and snapshot['lineMap'][i]==event['codeLine']:
            draw.rectangle((pad-8,y-3,size[0]-pad,y+layout['lineHeight']-3),fill='#2d3542')
            draw.polygon([(8,y+4),(20,y+11),(8,y+18)],fill='#f7b955')
        draw.text((pad,y),str(snapshot['lineMap'][i]),font=font,fill='#8491a3')
        for col,char in enumerate(line):
            draw.text((x0+font.getlength(line[:col]),y),char,font=font,fill=snapshot['colors'][offset])
            offset+=len(char.encode('utf-16-le'))//2
        offset+=1  # newline in the original semantic snapshot
    return image


def validate_track(file,size,fps,frames):
    with av.open(str(file)) as video:
        stream=video.streams.video[0]
        if (stream.width,stream.height)!=size or float(stream.average_rate)!=fps:
            raise ValueError('Track dimensions or FPS differ')
        if sum(1 for _ in video.decode(video=0))!=frames:
            raise ValueError('Track frame count differs')


def run(manifest,base):
    def file(key):
        return (base/manifest[key]).resolve()
    diagram_path,code_path=file('diagramImage'),file('codeSnapshot')
    inputs=[diagram_path,code_path,file('font')]
    source=json.loads(code_path.read_text(encoding='utf-8-sig'))
    source_file=Path(source['source'])
    if not source_file.is_absolute(): source_file=code_path.parent/source_file
    actual=source_file.read_text(encoding='utf-8-sig').splitlines()
    if any(n<1 or n>len(actual) or line!=actual[n-1] for line,n in zip(source['code'].split('\n'),source['lineMap'])):
        raise ValueError('Code snapshot differs from source file')
    inputs.append(source_file)
    width,height=manifest['canvas']['width'],manifest['canvas']['height']
    fps=manifest['canvas']['fps'];duration=manifest['durationSeconds']
    if not all(isinstance(n,int) and n>=64 and n%2==0 for n in (width,height)) or not isinstance(fps,int) or not 1<=fps<=60 or not 0<duration<=3600:
        raise ValueError('Invalid canvas or duration')
    rects=manifest['tracks']
    for rect in rects.values():
        if not all(isinstance(rect[k],int) and rect[k]>=0 for k in ('x','y','width','height')) or min(rect['width'],rect['height'])<64 or rect['width']%2 or rect['height']%2:
            raise ValueError('Invalid track rectangle')
        if rect['x']+rect['width']>width or rect['y']+rect['height']>height:
            raise ValueError('Track exceeds canvas')
    d,c=rects['diagram'],rects['code']
    if d['x']<c['x']+c['width'] and c['x']<d['x']+d['width'] and d['y']<c['y']+c['height'] and c['y']<d['y']+d['height']:
        raise ValueError('Independent tracks overlap')
    ds=(d['width'],d['height']);cs=(c['width'],c['height'])
    with Image.open(diagram_path) as original:
        original=ImageOps.exif_transpose(original).convert('RGB')
        original_size=original.size
        fitted=ImageOps.contain(original,(ds[0]-32,ds[1]-32))
    diagram=Image.new('RGB',ds,'white');dx=(ds[0]-fitted.width)//2;dy=(ds[1]-fitted.height)//2
    diagram.paste(fitted,(dx,dy))
    layout=fit_code(source,cs,file('font'),manifest.get('minimumCodeFontSize',18),manifest.get('codeFontSize',30))
    events=manifest.get('events',[])
    if any(not 0<=e['time']<duration for e in events) or any(a['time']>b['time'] for a,b in zip(events,events[1:])):
        raise ValueError('Events must be ordered and within the clip')
    geo=None
    if events:
        inputs.append(file('diagramGeometry'));geo=json.loads(file('diagramGeometry').read_text(encoding='utf8'))
        if (geo['width'],geo['height'])!=original_size: raise ValueError('Diagram geometry differs from image')
        for e in events:
            if e['codeLine'] not in source['lineMap'] or e['diagramCell'] not in geo['cells']:
                raise ValueError('Event target missing from an independent scene')
    audio=file('audio') if manifest.get('audio') else None
    if audio:
        inputs.append(audio)
        with av.open(str(audio)) as media:
            if not media.streams.audio or media.duration is None or media.duration/av.time_base<duration-.05:
                raise ValueError('Prepared audio is shorter than clip')
    hashes={str(f):digest(f) for f in inputs}
    out=Path(tempfile.mkdtemp(prefix='independent-scenes-',dir=material_dir()))
    (out/'composition.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    frames=math.ceil(duration*fps-1e-9);ff=imageio_ffmpeg.get_ffmpeg_exe()
    def render_frame(name,t):
        event=next((e for e in reversed(events) if e['time']<=t),None)
        if name=='code': return code_frame(source,layout,cs,event)
        image=diagram.copy()
        if event:
            box=geo['cells'][event['diagramCell']]
            sx,sy=fitted.width/original_size[0],fitted.height/original_size[1]
            x=dx+box['x']*sx;y=dy+box['y']*sy
            right=x+box['width']*sx;bottom=y+box['height']*sy
            if x<dx or y<dy or right>dx+fitted.width+1 or bottom>dy+fitted.height+1:
                raise ValueError('Diagram target is clipped in its export')
            ImageDraw.Draw(image).rectangle((x-2,y-2,right+2,bottom+2),outline='#d34224',width=3)
        return image
    # Separate files are the editable source tracks; composition never crops them.
    for name,size in [('diagram',ds),('code',cs)]:
        target=out/(name+'.mp4')
        cmd=[ff,'-nostdin','-n','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{size[0]}x{size[1]}','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(target)]
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        try:
            for i in range(frames):process.stdin.write(render_frame(name,i/fps).tobytes())
            process.stdin.close()
            if process.wait()!=0:raise RuntimeError('Track encoding failed')
        finally:
            if process.poll() is None:process.kill();process.wait()
        validate_track(target,size,fps,frames)
        render_frame(name,min(duration/2,(frames-1)/fps)).save(out/(name+'.png'))
    filters=f"color=c=0x172536:s={width}x{height}:r={fps}:d={frames/fps}[base];[base][0:v]overlay={d['x']}:{d['y']}:shortest=1[left];[left][1:v]overlay={c['x']}:{c['y']}:shortest=1[v]"
    cmd=[ff,'-nostdin','-n','-hide_banner','-loglevel','error','-i',str(out/'diagram.mp4'),'-i',str(out/'code.mp4')]
    if audio:cmd+=['-i',str(audio)]
    cmd+=['-filter_complex',filters,'-map','[v]']
    if audio:cmd+=['-map','2:a:0','-c:a','aac','-b:a','192k']
    cmd+=['-t',str(frames/fps),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'composed.mp4')]
    subprocess.run(cmd,check=True);validate_track(out/'composed.mp4',(width,height),fps,frames)
    preview=Image.new('RGB',(width,height),'#172536')
    for name,r in [('diagram',d),('code',c)]:preview.paste(render_frame(name,min(duration/2,(frames-1)/fps)),(r['x'],r['y']))
    preview.save(out/'composed.png')
    if any(digest(f)!=h for f,h in hashes.items()):raise ValueError('Source changed during render')
    report={'output':str(out),'tracks':['diagram.mp4','code.mp4'],'composition':'composed.mp4','frames':frames,'fps':fps,'sourceHashes':hashes,'codeFontSize':layout['fontSize'],'diagramFit':'contain, no crop','sourceAssetsUnchanged':True,'editorWindowCaptureUsed':False,'events':len(events)}
    (out/'composition-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);args=parser.parse_args()
    manifest=args.manifest.resolve()
    print(json.dumps(run(json.loads(manifest.read_text(encoding='utf-8-sig')),manifest.parent),ensure_ascii=True))
