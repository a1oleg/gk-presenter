"""Join the recorded menu action and the subsequent real panel resize."""
import json,subprocess
from pathlib import Path
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1]
head=json.loads((root/'output/interactive-row011-1789395201269/recording.json').read_text(encoding='utf8'))
tail=json.loads((root/'output/interactive-row011-1789395233398/recording.json').read_text(encoding='utf8'))
out=root/'output/interactive-row011-1789395233398'
cut=next(e['time'] for e in head['events'] if e['input']['action']=='waitForAnalysis')+.2
video=out/'recording-combined.mp4'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-n','-i',head['outputPath'],'-i',tail['outputPath'],'-filter_complex',f'[0:v]trim=end={cut},setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v]','-map','[v]','-an','-c:v','libx264','-crf','18','-preset','fast',str(video)],check=True)
for e in tail['events']:e['time']+=cut
report={**head,'outputPath':str(video),'events':head['events']+tail['events'],'sourceRecordings':[head['outputPath'],tail['outputPath']]}
(out/'recording-combined.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
