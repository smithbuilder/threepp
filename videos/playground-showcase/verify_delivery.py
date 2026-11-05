"""Verify the delivered MP4 and make a sheet of decoded frames for visual review."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
VIDEO = ROOT / 'outputs/Vehicle-Playground-Showcase.mp4'
PROOF = ROOT / 'proof'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


probe = json.loads(subprocess.check_output([
    'ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json',
    str(VIDEO),
], text=True))
(PROOF / 'delivery-probe.json').write_text(json.dumps(probe, indent=2), encoding='utf-8')
picture = next(s for s in probe['streams'] if s['codec_type'] == 'video')
audio = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
assert (picture['width'], picture['height']) == (960, 600)
assert picture['avg_frame_rate'] == '30/1'
assert int(picture['nb_frames']) == 2400
assert float(probe['format']['duration']) == 80
assert audio['codec_name'] == 'aac' and audio['channels'] == 2
with (PROOF / 'decode.log').open('w', encoding='utf-8') as log:
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-threads', '2',
                    '-i', str(VIDEO), '-f', 'null', '-'], stderr=log, check=True)
assert (PROOF / 'decode.log').stat().st_size == 0
with (PROOF / 'audio-measurement.log').open('w', encoding='utf-8') as log:
    subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-threads', '2',
                    '-i', str(VIDEO), '-vn', '-af', 'ebur128=peak=true',
                    '-f', 'null', '-'], stderr=log, check=True)
summary = (PROOF / 'audio-measurement.log').read_text(encoding='utf-8').rsplit('Summary:', 1)[1]
integrated = float(re.search(r'I:\s+(-?[\d.]+) LUFS', summary).group(1))
true_peak = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', summary).group(1))
assert true_peak < 0

times = [5, 16, 24.5, 28, 45, 61, 74, 77.5]
selection = '+'.join(f'eq(n\\,{round(t * 30)})' for t in times)
subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-threads', '2',
                '-i', str(VIDEO), '-vf', f'select={selection}', '-fps_mode', 'vfr',
                '-frames:v', '8', '-threads', '2', str(PROOF / 'decoded-%02d.png')], check=True)
frames = []
font = ImageFont.truetype(str(ROOT / 'assets/fonts/Barlow-Regular.ttf'), 22)
sheet = Image.new('RGB', (1152, 4 * 396), '#24271f')
draw = ImageDraw.Draw(sheet)
for n, time in enumerate(times, 1):
    path = PROOF / f'decoded-{n:02d}.png'
    with Image.open(path) as im:
        assert im.size == (960, 600)
        sheet.paste(im.resize((576, 360)), (((n - 1) % 2) * 576, ((n - 1) // 2) * 396 + 36))
    draw.text((((n - 1) % 2) * 576 + 12, ((n - 1) // 2) * 396 + 5),
              f'Decoded export | {time:g} seconds', font=font, fill='#fff8e8')
    frames.append({'timeSeconds': time, 'path': str(path.relative_to(ROOT)), 'sha256': digest(path)})
sheet.save(ROOT / 'outputs/Review-frames.jpg', quality=94)

receipt = {
    'output': str(VIDEO.relative_to(ROOT)),
    'sha256': digest(VIDEO),
    'bytes': VIDEO.stat().st_size,
    'durationSeconds': 80,
    'width': 960, 'height': 600, 'fps': 30, 'frameCount': 2400,
    'videoCodec': picture['codec_name'], 'audioCodec': audio['codec_name'],
    'fullDecode': {'passed': True, 'log': 'proof/decode.log'},
    'audio': {'integratedLufs': integrated, 'truePeakDbfs': true_peak,
              'measurement': 'proof/audio-measurement.log',
              'signalAnalysis': 'proof/audio-analysis.json', 'listeningReviewed': False},
    'decodedFrames': frames,
    'compositionCheck': 'proof/check-final.json',
    'renderLog': 'proof/render.log',
    'renderer': 'HyperFrames 0.9.16; software browser; CPU encoding; one worker',
    'sourceFiles': {name: digest(ROOT / name) for name in [
        'source-manifest.json', 'voice-receipt.json', 'edit-manifest.json',
        'narration.json', 'index.html',
    ]},
    'sceneFiles': {str(path.relative_to(ROOT)): digest(path)
                   for path in sorted((ROOT / 'compositions').glob('*.html'))},
    'limitations': [
        'Safari stalls before the steep-hill crest in the longer assisted run; disclosed in film.',
        'Simplified raycast suspension and estimated aero coefficients; not CFD.',
        'Narration and music levels measured; no human listening review.',
        'Motion and driving feel remain subject to hands-on user acceptance.',
    ],
}
(ROOT / 'outputs/delivery-receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps({'verified': True, 'sha256': receipt['sha256'], 'bytes': receipt['bytes']}, indent=2))
