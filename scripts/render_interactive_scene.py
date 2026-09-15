"""Align recorded UI milestones to spoken anchors; never retime or reuse mic audio."""
import argparse,json,math,subprocess
from pathlib import Path
import av,imageio_ffmpeg

p=argparse.ArgumentParser()
p.add_argument('audio_directory',type=Path)
p.add_argument('recording_report',type=Path)
p.add_argument('--suffix',default='')
p.add_argument('--case-demo',action='store_true')
args=p.parse_args()
out=args.audio_directory.resolve()
recording=json.loads(args.recording_report.read_text(encoding='utf8'))
alignment=json.loads((out/'alignment.json').read_text(encoding='utf8'))['alignment']
text=''.join(alignment['characters'])
def anchor(value):
    assert text.count(value)==1
    return alignment['character_start_times_seconds'][text.index(value)]
audio=out/'speech.mp3'
with av.open(str(audio)) as c: duration=c.duration/1e6
duration=math.ceil((duration+.3)*30)/30
if args.case_demo:
    case_events=[e for e in recording['events'] if e['input']['action']=='selectCase']
    menu=case_events[0]['time'];loaded=case_events[-1]['time']
    first_anchor='Нажимая на кейсы';last_anchor='до последнего случая'
else:
    menu=next(e for e in recording['events'] if e['input']['action']=='contextMenu')['time']
    loaded=next(e for e in recording['events'] if e['input']['action']=='waitForAnalysis')['time']
    first_anchor='откроем';last_anchor='Здесь'
spoken_menu=anchor(first_anchor)
spoken_loaded=anchor(last_anchor)
filters=[]
for i,(start,end,target) in enumerate([(0,menu,spoken_menu),(menu,loaded,spoken_loaded-spoken_menu),(loaded,loaded+duration-spoken_loaded,duration-spoken_loaded)]):
    filters.append(f'[0:v]trim=start={start}:end={end},setpts=(PTS-STARTPTS)*{target/(end-start)},fps=30,setsar=1[v{i}]')
filters.append('[v0][v1][v2]concat=n=3:v=1:a=0,fps=30,format=yuv420p[v]')
filters.append(f'[1:a]apad,atrim=duration={duration},asetpts=PTS-STARTPTS[a]')
video=out/f'scene-interactive{args.suffix}.mp4'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-n','-i',recording['outputPath'],'-i',str(audio),'-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','libx264','-preset','medium','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart','-t',str(duration),str(video)],check=True)
with av.open(str(video)) as c:
    v=c.streams.video[0]
    assert (v.width,v.height)==(1600,900)
    assert c.streams.audio
    frames=0
    for f in c.decode(video=0):
        if frames in [105,240]: f.to_image().save(out/f'capture-check-{frames}.png')
        frames+=1
    assert abs(frames/30-duration)<.1
report={'video':str(video),'sourceRecording':recording['outputPath'],'duration':duration,'frames':frames,'audioSource':str(audio),'microphoneAudioUsed':False,'markers':[{'anchor':first_anchor,'time':spoken_menu,'sourceTime':menu},{'anchor':last_anchor,'time':spoken_loaded,'sourceTime':loaded}]}
(out/f'interactive-video-report{args.suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
