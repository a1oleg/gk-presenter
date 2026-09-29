from material_paths import material_dir
"""Join scenes in the supplied order, retaining exact frame counts and cut timing."""
import argparse,hashlib,json,subprocess,time,re
from pathlib import Path
import av
import imageio_ffmpeg

parser=argparse.ArgumentParser()
parser.add_argument('videos',type=Path,nargs='*')
parser.add_argument('--sheet-snapshot',type=Path)
parser.add_argument('--canvas',default='1920x1080')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
out=material_dir('output')/f'joined-scenes-{time.time_ns()}'
out.mkdir()
records=[];inputs=[];filters=[];streams=[];cursor=0
rows=[]
if args.sheet_snapshot:
    snapshot=json.loads(args.sheet_snapshot.read_text(encoding='utf-8'))
    column=snapshot['values'][0].index('ссылка на видео')
    rows=[(i+1,Path(re.sub(r'^/([A-Za-z]:/)',r'\1',row[column].strip().strip('"')))) for i,row in enumerate(snapshot['values']) if i and len(row)>column and row[column].strip()]
    args.videos=[p for _,p in rows]
    (out/'sheet-source.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
assert args.videos,'No completed videos selected'
width,height=map(int,args.canvas.split('x'))
print(f'Joining {len(args.videos)} scenes into {out}',flush=True)
for i,p in enumerate(args.videos):
    p=p.resolve();assert p.is_file()
    with av.open(str(p)) as container:
        v=container.streams.video[0];has_audio=bool(container.streams.audio)
        assert abs(float(v.average_rate)-30)<0.01, f'Unexpected FPS: {p}: {v.average_rate}'
        frames=sum(1 for _ in container.decode(video=0))
    duration=frames/30
    records.append({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'frames':frames,'startSeconds':cursor,'durationSeconds':duration})
    if rows: records[-1]['sheetRow']=rows[i][0]
    print(f'Checked scene {i+1}/{len(args.videos)}: {frames} frames, {duration:.2f}s',flush=True)
    cursor+=duration
    inputs+=['-threads','1','-i',str(p)]
    filters+=[f'[{i}:v:0]settb=1/30,setpts=N,scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x292929,setsar=1[v{i}]']
    filters += [f'[{i}:a:0]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=duration={duration:.9f},asetpts=PTS-STARTPTS[a{i}]' if has_audio else f'anullsrc=r=44100:cl=stereo,atrim=duration={duration:.9f},asetpts=PTS-STARTPTS[a{i}]']
    streams += [f'[v{i}][a{i}]']
filters += [''.join(streams)+f'concat=n={len(records)}:v=1:a=1[v][a]']
target=out/(f'graphKoda-ready-{rows[0][0]:02d}-{rows[-1][0]:02d}.mp4' if rows else 'scenes-joined.mp4')
print(f'Encoding {cursor:.2f}s',flush=True)
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error',*inputs,
    '-filter_complex_threads','1','-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','libx264','-threads','4','-preset','fast','-crf','18',
    '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(target)],check=True)
with av.open(str(target)) as c:
    actual=sum(1 for _ in c.decode(video=0))
    duration=c.duration/av.time_base
assert actual==sum(r['frames'] for r in records)
with av.open(str(target)) as c:
    samples=sum(f.samples for f in c.decode(audio=0))
assert abs(samples/44100-cursor)<0.1
assert all(hashlib.sha256(Path(r['file']).read_bytes()).hexdigest()==r['sha256'] for r in records)
report={'output':str(target),'seconds':duration,'frames':actual,'sources':records,'audioSamples':samples,'transitions':False,'originalFilesUnchanged':True}
(out/'join-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='sources'},ensure_ascii=False))
