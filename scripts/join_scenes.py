"""Join scenes in the supplied order, retaining exact frame counts and cut timing."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import av
import imageio_ffmpeg

parser=argparse.ArgumentParser()
parser.add_argument('videos',type=Path,nargs='*')
parser.add_argument('--sheet-snapshot',type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
out=root/'output'/f'joined-scenes-{time.time_ns()}'
out.mkdir()
records=[];inputs=[];filters=[];streams=[];cursor=0
rows=[]
if args.sheet_snapshot:
    snapshot=json.loads(args.sheet_snapshot.read_text(encoding='utf-8'))
    rows=[(i+1,Path(row[7].strip().strip('"'))) for i,row in enumerate(snapshot['values']) if i and len(row)>7 and row[7]]
    args.videos=[p for _,p in rows]
    (out/'sheet-source.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
assert args.videos,'No completed videos selected'
print(f'Joining {len(args.videos)} scenes into {out}',flush=True)
for i,p in enumerate(args.videos):
    p=p.resolve();assert p.is_file()
    with av.open(str(p)) as container:
        v=container.streams.video[0];a=container.streams.audio[0]
        assert v.average_rate==30 and (v.width,v.height)==(1600,900)
        frames=sum(1 for _ in container.decode(video=0))
    duration=frames/30
    records.append({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'frames':frames,'startSeconds':cursor,'durationSeconds':duration})
    if rows: records[-1]['sheetRow']=rows[i][0]
    print(f'Checked scene {i+1}/{len(args.videos)}: {frames} frames, {duration:.2f}s',flush=True)
    cursor+=duration
    inputs+=['-threads','1','-i',str(p)]
    filters+=[f'[{i}:v:0]setpts=PTS-STARTPTS,setsar=1[v{i}]',
              f'[{i}:a:0]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=duration={duration:.9f},asetpts=PTS-STARTPTS[a{i}]']
    streams += [f'[v{i}][a{i}]']
filters += [''.join(streams)+f'concat=n={len(records)}:v=1:a=1[v][a]']
target=out/(f'coldKode-ready-{rows[0][0]:02d}-{rows[-1][0]:02d}.mp4' if rows else 'scenes-joined.mp4')
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
