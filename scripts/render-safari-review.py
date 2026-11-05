"""Encode supervised native takes and their logged runtime exhaust controls.

CPU only. This does not launch the engine or authorize captures. Each manifest
clip names a session under build/sessions; captures must already have passed
the supervisor. No scaling, interpolation, generated picture or native player.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RATE = 48000
FPS = 30


def sha(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def run(args, log=None):
    result = subprocess.run(args, capture_output=True, check=False)
    if log:
        log.write_bytes(result.stderr)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed: {result.stderr.decode(errors="replace")[-3000:]}')
    return result


def measure(path):
    r = run(['ffmpeg', '-nostdin', '-hide_banner', '-threads', '2', '-i', str(path),
             '-vn', '-filter_threads', '1', '-af', 'ebur128=peak=true', '-f', 'null', '-'])
    summary = r.stderr.decode(errors='replace').rsplit('Summary:', 1)[-1]
    return {'lufs': float(re.search(r'I:\s*([-\d.]+) LUFS', summary)[1]),
            'truePeakDb': float(re.search(r'Peak:\s*([-\d.]+) dBFS', summary)[1])}


def write_wave(path, samples):
    data = np.round(np.clip(samples, -.9999, .9999) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as output:
        output.setparams((2, 2, RATE, 0, 'NONE', 'not compressed'))
        output.writeframes(np.repeat(data[:, None], 2, axis=1).tobytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise RuntimeError('Preserve prior review videos; choose a new output path.')
    proof = output.parent / (output.stem + '-proof')
    proof.mkdir(exist_ok=True)
    clips, records, rows = [], [], []
    for index, clip in enumerate(manifest['clips']):
        session_name = clip['session']
        if not re.fullmatch(r'\d{8}-\d{6}-\d{3}', session_name):
            raise ValueError('Manifest must name an existing supervised session.')
        session = ROOT / 'build/sessions' / session_name
        result = json.loads((session / 'result.json').read_text(encoding='utf-8-sig'))
        assert result['exitCode'] == 0 and result['reason'] == 'exited'
        assert result['vehicle'] == 'safari' and result['sequence'] and result['captureScale'] == 1
        assert result['renderWidth'] == 960 and result['renderHeight'] == 600
        assert result['binarySha256'].lower() == manifest['binarySha256'].lower()
        assert result['vehicleAssetSha256'].lower() == manifest['modelSha256'].lower()
        assert (session / 'stderr.log').stat().st_size == 0
        frames = session / 'frames'
        paths = sorted(frames.glob('frame_*.png'))
        assert len(paths) == clip['frames'] == result['requestedFrames']
        hashes = []
        for n, path in enumerate(paths):
            assert path.name == f'frame_{n:05d}.png'
            with Image.open(path) as im:
                assert im.size == (960, 600)
            hashes.append(sha(path))
        with (frames / 'frame-data.csv').open(newline='', encoding='utf-8-sig') as f:
            state = list(csv.DictReader(f))
        assert len(state) == len(paths)
        for n, row in enumerate(state):
            assert int(row['frame']) == n
            for band in range(3):
                assert np.isfinite(float(row[f'exhaustPitch{band}']))
                assert np.isfinite(float(row[f'exhaustGain{band}']))
                assert float(row[f'exhaustPitch{band}']) > 0 and float(row[f'exhaustGain{band}']) >= 0
        movie = proof / f'{index:02d}.mp4'
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(frames / 'frame_%05d.png'),
             '-frames:v', str(len(paths)), '-an', '-c:v', 'libx264', '-threads', '2', '-filter_threads', '1',
             '-preset', 'medium', '-crf', '16', '-vf', 'scale=iw:ih:out_color_matrix=bt709:out_range=tv,format=yuv420p',
             '-colorspace', 'bt709', str(movie)], proof / f'{index:02d}-encode.log')
        clips.append(movie)
        records.append({'label': clip['label'], 'session': session_name, 'frames': len(paths),
                        'frameHashesDigest': hashlib.sha256(''.join(hashes).encode()).hexdigest(),
                        'frameHashes': hashes, 'resultSha256': sha(session / 'result.json'),
                        'csvSha256': sha(frames / 'frame-data.csv'), 'encodedSha256': sha(movie)})
        rows.extend(state)
    count = len(rows)
    duration = count / FPS
    t = np.arange(round(duration * RATE)) / RATE
    frame_times = np.arange(count) / FPS
    mix = np.zeros(len(t))
    sources = []
    for band, name in enumerate(('idle', 'mid', 'high')):
        source = ROOT / 'showcase/assets' / f'safari_exhaust_{name}.wav'
        with wave.open(str(source), 'rb') as f:
            assert f.getframerate() == RATE and f.getnchannels() == 1 and f.getsampwidth() == 2
            samples = np.frombuffer(f.readframes(f.getnframes()), dtype='<i2').astype(float) / 32768
        pitch = np.interp(t, frame_times, [float(r[f'exhaustPitch{band}']) for r in rows])
        gain = np.interp(t, frame_times, [float(r[f'exhaustGain{band}']) for r in rows])
        phase = np.mod(np.cumsum(pitch) - pitch, len(samples))
        left = np.floor(phase).astype(int)
        blend = phase - left
        mix += (samples[left] * (1-blend) + samples[(left+1) % len(samples)] * blend) * gain
        sources.append({'file': str(source.relative_to(ROOT)), 'sha256': sha(source)})
    fade = min(round(.025 * RATE), len(mix) // 2)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)
    audio = proof / 'exhaust.wav'
    assert np.max(np.abs(mix)) < 1, 'Runtime mix clips before movie gain'
    write_wave(audio, mix)
    before = measure(audio)
    gain_db = min(-18-before['lufs'], -3-before['truePeakDb'])
    mix *= 10**(gain_db/20)
    assert np.max(np.abs(mix)) < 1
    write_wave(audio, mix)
    listing = proof / 'concat.txt'
    listing.write_text(''.join(f"file '{p.name}'\n" for p in clips), encoding='utf-8')
    silent = proof / 'native-picture.mp4'
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(listing),
         '-c', 'copy', str(silent)], proof / 'concat.log')
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(silent), '-i', str(audio), '-c:v', 'copy',
         '-c:a', 'aac', '-threads', '2', '-b:a', '192k', '-ar', str(RATE), '-movflags', '+faststart',
         '-shortest', str(output)], proof / 'mux.log')
    probe = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(output)]).stdout)
    video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    assert video['width'] == 960 and video['height'] == 600 and video['avg_frame_rate'] == '30/1'
    assert int(video['nb_frames']) == count and abs(float(probe['format']['duration']) - duration) < .05
    decode = run(['ffmpeg', '-nostdin', '-v', 'error', '-threads', '2', '-i', str(output), '-f', 'null', '-'], proof / 'decode.log')
    assert not decode.stderr
    audio_measurement = measure(output)
    assert audio_measurement['truePeakDb'] < 0
    (proof / 'probe.json').write_text(json.dumps(probe, indent=2) + '\n')
    source_receipt = ROOT / 'showcase/assets/SAFARI-EXHAUST-SOURCE.json'
    receipt = {'scope': 'native iteration review candidate; human movement/sound acceptance separate',
               'picture': 'Original threepp960x600/30FPS framebuffer images; no upscale or interpolation',
               'audio': 'Same Safari recorded samples and per-band controls logged by runtime; reconstructed, not endpoint audio',
               'modelSha256': manifest['modelSha256'], 'binarySha256': manifest['binarySha256'],
               'manifestSha256': sha(args.manifest), 'rendererScriptSha256': sha(Path(__file__)),
               'clips': records, 'audioSources': sources, 'movieGainDb': gain_db,
               'sourceAudioReceiptSha256': sha(source_receipt),
               'sourceAudioCredit': json.loads(source_receipt.read_text(encoding='utf-8-sig')),
               'audioMeasurement': audio_measurement, 'frames': count, 'seconds': duration,
               'outputSha256': sha(output), 'bytes': output.stat().st_size, 'fullDecodePassed': True}
    (proof / 'provenance.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('clips', 'audioSources')}, indent=2))


if __name__ == '__main__':
    main()
