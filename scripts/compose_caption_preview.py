import json,subprocess,sys
from pathlib import Path
import imageio_ffmpeg
out=Path(sys.argv[1]).resolve()
meta=json.loads((out/'clearance.json').read_text(encoding='utf8'))
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-hide_banner','-loglevel','error','-ss','4.666667','-i',meta['recording'],'-i',str(out/'caption-frames/00140.png'),'-filter_complex','[0:v][1:v]overlay=0:0:format=auto[out]','-map','[out]','-frames:v','1',str(out/'preview.png')],check=True)
print(out/'preview.png')
