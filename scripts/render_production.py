"""Render a compiled lesson with generic image/text/pointer layers and prepared audio.

No network calls, speech synthesis or publication. All media goes to configured materials.
"""
import argparse, hashlib, json, math, subprocess, sys
from pathlib import Path
from fractions import Fraction
import av
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageOps
from material_paths import material_dir


def verify_assets(plan):
    for item in plan['assets']:
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Source changed: ' + item['path'])


def audio_duration(file):
    with av.open(file) as media:
        if not media.streams.audio:
            raise ValueError('Audio file has no audio stream')
        stream = media.streams.audio[0]
        # Decode the selected stream; container duration can include unrelated video.
        seconds = float(sum((Fraction(frame.samples, frame.sample_rate) for frame in media.decode(stream)), Fraction()))
    if not 0 < seconds <= 3600:
        raise ValueError('Audio duration must be in (0,3600]')
    return seconds


def prepare(plan):
    verify_assets(plan)
    width, height, fps = (plan['canvas'][k] for k in ('width', 'height', 'fps'))
    prepared = []
    for scene in plan['scenes']:
        seconds = audio_duration(scene['audio']['path']) if scene['audio']['mode'] == 'file' else scene['durationSeconds']
        frames = math.ceil((seconds + scene['tailSeconds']) * fps - 1e-9)
        duration = frames / fps
        image = Image.new('RGB', (width, height), plan['background'])
        if scene['background']['kind'] == 'image':
            with Image.open(scene['background']['asset']['path']) as original:
                fitted = ImageOps.contain(ImageOps.exif_transpose(original).convert('RGBA'), (width, height))
                image.paste(fitted, ((width-fitted.width)//2, (height-fitted.height)//2), fitted)
        layers = []
        for overlay in scene['overlays']:
            if overlay['start'] >= duration or (overlay['end'] is not None and overlay['end'] > duration):
                raise ValueError(f"{scene['id']}: overlay timing outside scene")
            x, y = round(overlay['x'] * width), round(overlay['y'] * height)
            layer = dict(overlay, px=x, py=y)
            if overlay['kind'] == 'text':
                font = ImageFont.truetype(plan['font']['path'], overlay['size'])
                box = ImageDraw.Draw(image).multiline_textbbox((0, 0), overlay['text'], font=font, spacing=6)
                w, h = box[2]-box[0], box[3]-box[1]
                if x < 0 or y < 0 or x+w > width or y+h > height:
                    raise ValueError(f"{scene['id']}: text does not fit canvas")
                layer.update(font=font, offset=(-box[0], -box[1]))
            elif x + overlay['size'] > width or y + overlay['size'] > height:
                raise ValueError(f"{scene['id']}: pointer does not fit canvas")
            layers.append(layer)
        prepared.append(dict(scene=scene, background=image, layers=layers, frames=frames, duration=duration, audioSeconds=seconds))
    return prepared


def frame_at(item, t):
    image = item['background'].copy()
    draw = ImageDraw.Draw(image)
    for layer in item['layers']:
        if t < layer['start'] or (layer['end'] is not None and t >= layer['end']):
            continue
        x, y = layer['px'], layer['py']
        if layer['kind'] == 'text':
            dx, dy = layer['offset']
            draw.multiline_text((x+dx, y+dy), layer['text'], font=layer['font'], fill=layer['color'], spacing=6)
        else:
            size = layer['size']
            draw.polygon([(x, y), (x+size, y+size//2), (x+size//2, y+size)], fill=layer['color'])
    return image


def inspect_video(file, canvas, expected_frames):
    with av.open(str(file)) as media:
        if len(media.streams.video) != 1 or len(media.streams.audio) != 1:
            raise ValueError('Expected exactly one audio and one video stream')
        stream = media.streams.video[0]
        if (stream.width, stream.height) != (canvas['width'], canvas['height']) or float(stream.average_rate) != canvas['fps']:
            raise ValueError('Unexpected output dimensions or FPS')
        frames = sum(1 for _ in media.decode(video=0))
        if frames != expected_frames:
            raise ValueError(f'Frame count differs: {frames} != {expected_frames}')
    with av.open(str(file)) as media:
        audio_seconds = sum(f.samples/f.sample_rate for f in media.decode(audio=0))
    if abs(audio_seconds - expected_frames/canvas['fps']) > 0.1:
        raise ValueError('Output audio duration differs from video')
    return dict(frames=frames, audioSeconds=audio_seconds)


def render(plan, prepared, out):
    root = material_dir().resolve()
    out = out.resolve()
    if out == root or not out.is_relative_to(root):
        raise ValueError('Output must be within configured material output')
    width, height, fps = (plan['canvas'][k] for k in ('width', 'height', 'fps'))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    records = []
    for item in prepared:
        scene = item['scene']
        target = out / (scene['id'] + '.mp4')
        cmd = [ffmpeg, '-nostdin', '-n', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{width}x{height}', '-r', str(fps), '-i', 'pipe:0']
        if scene['audio']['mode'] == 'file':
            cmd += ['-i', scene['audio']['path']]
        else:
            cmd += ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
        cmd += ['-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2','-af','apad','-t',str(item['duration']),'-movflags','+faststart',str(target)]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for frame in range(item['frames']):
                process.stdin.write(frame_at(item, frame/fps).tobytes())
            process.stdin.close()
            if process.wait() != 0:
                raise RuntimeError('Scene encoding failed')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
        check = inspect_video(target, plan['canvas'], item['frames'])
        # Representative frames are useful for human and agent review.
        for suffix, t in [('start',0),('middle',item['duration']/2)]:
            frame_at(item,t).save(out / f"{scene['id']}-{suffix}.png")
        records.append(dict(id=scene['id'],video=str(target),duration=item['duration'],audioMode=scene['audio']['mode'],claimIds=scene['claimIds'],**check))
    inputs, filters, streams = [], [], []
    for i, record in enumerate(records):
        inputs += ['-i', record['video']]
        filters += [f'[{i}:v]setpts=PTS-STARTPTS[v{i}]', f'[{i}:a]atrim=duration={record["duration"]},asetpts=PTS-STARTPTS[a{i}]']
        streams.append(f'[v{i}][a{i}]')
    filters.append(''.join(streams)+f'concat=n={len(records)}:v=1:a=1[v][a]')
    movie = out/'movie.mp4'
    subprocess.run([ffmpeg,'-nostdin','-n','-hide_banner','-loglevel','error',*inputs,'-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-r',str(fps),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-movflags','+faststart',str(movie)],check=True)
    check = inspect_video(movie, plan['canvas'], sum(r['frames'] for r in records))
    verify_assets(plan)
    report = dict(version=1,title=plan['title'],video=str(movie),canvas=plan['canvas'],scenes=records,assets=plan['assets'],sourceAssetsUnchanged=True,**check)
    (out/'production-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    plan=json.load(sys.stdin)
    prepared=prepare(plan)
    if args.check:
        print(json.dumps(dict(ok=True,scenes=len(prepared),frames=sum(s['frames'] for s in prepared),canvas=plan['canvas'])))
    else:
        if not args.output:
            parser.error('--output required')
        print(json.dumps(render(plan,prepared,args.output),ensure_ascii=True))


if __name__ == '__main__':
    main()
