"""Replace narration while stream-copying every original video packet."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import av,imageio_ffmpeg
p=argparse.ArgumentParser();p.add_argument('video',type=Path);p.add_argument('audio',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
assert args.video.is_file() and args.audio.is_file() and not args.output.exists()
def video_fingerprint(path):
 with av.open(str(path)) as c:
  stream=c.streams.video[0];digest=hashlib.sha256();packets=0
  for packet in c.demux(stream):
   if packet.size: digest.update(bytes(packet));packets+=1
  return {'sha256':digest.hexdigest(),'packets':packets,'width':stream.width,'height':stream.height}
before=video_fingerprint(args.video)
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-n','-i',str(args.video),'-i',str(args.audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(args.output)],check=True)
assert video_fingerprint(args.output)==before,'Video packets changed'
with av.open(str(args.output)) as c:
 duration=c.duration/1e6
 assert sum(1 for _ in c.decode(audio=0))>0
report={'video':str(args.output.resolve()),'sourceVideo':str(args.video.resolve()),'audio':str(args.audio.resolve()),'durationSeconds':duration,'videoStreamUnchanged':True,'videoFingerprint':before}
args.output.with_suffix('.report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
