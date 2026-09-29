"""Render the exact screenshot from the captured sheet row, without overlays."""
import argparse,hashlib,json,math,shutil,subprocess
from pathlib import Path
import av
import imageio_ffmpeg
from PIL import Image

parser=argparse.ArgumentParser()
parser.add_argument('output',type=Path)
parser.add_argument('--row-index',type=int,default=1)
parser.add_argument('--audio',type=Path)
parser.add_argument('--background',type=Path,help='Resolved scene asset, e.g. a Google Slides export; preserves the original sheet snapshot')
parser.add_argument('--canvas',help='Optional WIDTHxHEIGHT; contain without cropping')
parser.add_argument('--no-upscale',action='store_true')
parser.add_argument('--background-color',default='black')
args=parser.parse_args();out=args.output.resolve()
snapshot=json.loads((out/'sheet-source.json').read_text(encoding='utf-8'))
source=args.background.resolve() if args.background else Path(snapshot['values'][args.row_index][1].strip().strip('"'))
audio_path=args.audio.resolve() if args.audio else out/'speech.mp3'
assert source.is_file()
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
with Image.open(source) as img:
    width,height=img.size
assert args.canvas or (width%2==0 and height%2==0)
source_width,source_height=width,height
filters=[]
if args.canvas:
    width,height=map(int,args.canvas.split('x'))
    assert width>0 and height>0 and width%2==0 and height%2==0
    if args.no_upscale and source_width<=width and source_height<=height:
        filters=['-vf',f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={args.background_color},setsar=1']
    elif args.no_upscale:
        filters=['-vf',f"scale=w='trunc(iw*min(1,min({width}/iw,{height}/ih))/2)*2':h='trunc(ih*min(1,min({width}/iw,{height}/ih))/2)*2',pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={args.background_color},setsar=1"]
    else:
        filters=['-vf',f'scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={args.background_color},setsar=1']
background=out/('background'+source.suffix)
if background.exists(): raise SystemExit('Background already exists; inspect before rerun')
shutil.copyfile(source,background)
with av.open(str(audio_path)) as audio:
    audio_duration=audio.duration/av.time_base
fps=30;frames=math.ceil((audio_duration+0.3)*fps);duration=frames/fps
video=out/'scene-static.mp4'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error',
    '-loop','1','-framerate',str(fps),'-i',str(background),'-i',str(audio_path),*filters,
    '-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-tune','stillimage','-crf','18',
    '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t',str(duration),
    '-movflags','+faststart',str(video)],check=True)
with av.open(str(video)) as check:
    assert len(check.streams.audio)==1 and len(check.streams.video)==1
    assert (check.streams.video[0].width,check.streams.video[0].height)==(width,height)
    decoded=sum(1 for _ in check.decode(video=0))
assert decoded==frames
with av.open(str(video)) as check:
    audio_samples=sum(f.samples for f in check.decode(audio=0))
assert audio_samples>0
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
report={'video':str(video),'source':str(source),'sourceSha256':source_hash,'width':width,'height':height,
        'audio':str(audio_path),'fit':('original size with padding' if args.no_upscale else 'contain with padding') if args.canvas else 'original size',
        'backgroundColor':args.background_color,
        'seconds':duration,'audioDuration':audio_duration,'decodedFrames':decoded,'audioSamples':audio_samples,
        'cursorAdded':False,'sourceUnchanged':True,'speechProcessing':False}
(out/'static-video-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
