"""CPU assembly of guarded native suspension replays, with source receipts.

Each clip remains 960x600/30fps. Only a small comparison caption is added.
The comparison is silent, so recorded/synthesized audio cannot bias the motion
comparison. This script never launches a game, graphics context or player.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(args, log):
    result = subprocess.run(args, capture_output=True, check=False)
    log.write_bytes(result.stderr)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace')[-3000:])
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError('Choose a new output; preserve prior review evidence.')
    proof = output.parent / (output.stem + '-proof')
    proof.mkdir(parents=True, exist_ok=True)
    font = str(ROOT / 'showcase/assets/Rajdhani-SemiBold.ttf').replace('\\', '/').replace(':', '\\:')
    records = []
    movies = []
    for index, clip in enumerate(manifest['clips']):
        assert re.fullmatch(r'\d{8}-\d{6}-\d{3}', clip['session'])
        assert re.fullmatch(r'[A-Za-z0-9 .-]+', clip['label'])
        session = ROOT / 'build/sessions' / clip['session']
        result = json.loads((session / 'result.json').read_text(encoding='utf-8-sig'))
        assert result['reason'] == 'exited' and result['exitCode'] == 0
        assert result['sequence'] and result['captureScale'] == 1
        assert (result['renderWidth'], result['renderHeight']) == (960, 600)
        assert result['binarySha256'].lower() == manifest['binarySha256'].lower()
        assert result['rideReplaySha256'].lower() == manifest['replaySha256'].lower()
        assert result['replayStartFrame'] == manifest['replayStartFrame']
        assert result['vehicle'] == clip['vehicle'] and result['safariRideProfile'] == clip['profile']
        assert not result['wheelInspect']
        if clip['vehicle'] == 'safari':
            assert result['vehicleAssetSha256'].lower() == manifest['modelSha256'].lower()
        assert (session / 'stderr.log').stat().st_size == 0
        frame_dir = session / 'frames'
        paths = sorted(frame_dir.glob('frame_*.png'))
        assert len(paths) == clip['frames'] == result['requestedFrames']
        with (frame_dir / 'frame-data.csv').open(newline='', encoding='utf-8-sig') as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == len(paths)
        frame_hashes = []
        for n, path in enumerate(paths):
            assert path.name == f'frame_{n:05d}.png' and int(rows[n]['frame']) == n
            with Image.open(path) as frame:
                assert frame.size == (960, 600)
            frame_hashes.append(sha(path))
        movie = proof / f'{index:02d}.mp4'
        caption = f"drawtext=fontfile='{font}':text='{clip['label']}':fontsize=24:fontcolor=0xf6f4e9:shadowcolor=black@0.65:shadowx=1:shadowy=2:x=32:y=92,format=yuv420p"
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-framerate', '30', '-i', str(frame_dir / 'frame_%05d.png'),
             '-frames:v', str(len(paths)), '-an', '-c:v', 'libx264', '-threads', '2', '-filter_threads', '1',
             '-preset', 'medium', '-crf', '16', '-vf', caption, str(movie)], proof / f'{index:02d}-encode.log')
        records.append({'label': clip['label'], 'session': clip['session'], 'resultSha256': sha(session / 'result.json'),
                        'csvSha256': sha(frame_dir / 'frame-data.csv'), 'frameHashes': frame_hashes,
                        'encodedSha256': sha(movie), 'nativeFrames': len(paths)})
        movies.append(movie)
    listing = proof / 'concat.txt'
    listing.write_text(''.join(f"file '{p.as_posix()}'\n" for p in movies), encoding='utf-8')
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(listing),
         '-c', 'copy', '-movflags', '+faststart', str(output)], proof / 'assembly.log')
    probe = run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(output)], proof / 'probe.log')
    (proof / 'probe.json').write_bytes(probe)
    run(['ffmpeg', '-nostdin', '-v', 'error', '-threads', '2', '-i', str(output), '-f', 'null', '-'], proof / 'full-decode.log')
    provenance = {'scope': 'Native-engine suspension comparison with captions; silent prescribed-input replay, not human control',
                  'binarySha256': manifest['binarySha256'], 'replaySha256': manifest['replaySha256'],
                  'outputSha256': sha(output), 'outputBytes': output.stat().st_size, 'clips': records}
    (proof / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(output), 'sha256': provenance['outputSha256'], 'bytes': provenance['outputBytes']}))


if __name__ == '__main__':
    main()
