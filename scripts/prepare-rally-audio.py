"""Prepare three looped exhaust bands from kyles' CC0 real dune-buggy recording.
Source: https://freesound.org/people/kyles/sounds/413905/
Usage: python scripts/prepare-rally-audio.py build/audio-source/buggy-kyles-413905.mp3
Requires ffmpeg. No generated oscillator sound or external service at runtime.
"""
import array
import hashlib
import json
import math
import pathlib
import subprocess
import sys
import tempfile
import wave

source = pathlib.Path(sys.argv[1])
target = pathlib.Path('showcase/assets')
bands = [('idle', 8.0, 2.4, 2600), ('mid', 17.0, 2.5, 3900), ('high', 21.0, 2.6, 5600)]
receipts = []
for name, start, duration, rpm in bands:
    with tempfile.TemporaryDirectory() as temp:
        decoded = pathlib.Path(temp) / 'decoded.wav'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(start), '-t', str(duration), '-i', str(source), '-ac', '1', '-ar', '48000', '-af', 'highpass=f=58,lowpass=f=4800', '-c:a', 'pcm_s16le', str(decoded)], check=True)
        with wave.open(str(decoded), 'rb') as reader:
            data = array.array('h', reader.readframes(reader.getnframes()))
        # Smooth the loop seam without smearing all the real combustion detail.
        fade = 7680
        blend = [data[-fade+i]*math.cos(i/fade*math.pi/2) + data[i]*math.sin(i/fade*math.pi/2) for i in range(fade)]
        loop = list(data[fade:-fade]) + blend
        mean = sum(loop)/len(loop)
        peak = max(abs(x-mean) for x in loop)
        output = array.array('h', (round((x-mean)/peak*24000) for x in loop))
        dest = target / f'cinder_exhaust_{name}.wav'
        with wave.open(str(dest), 'wb') as writer:
            writer.setnchannels(1); writer.setsampwidth(2); writer.setframerate(48000)
            writer.writeframes(output.tobytes())
        receipts.append({'file': dest.name, 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(), 'sourceStartSeconds': start, 'sourceDurationSeconds': duration, 'playbackBandRpm': rpm, 'processing': 'mono 48k PCM16; 58Hz highpass; 4.8kHz lowpass; 160ms circular equal-power seam; DC removal; peak -2.7dBFS'})
receipt = {'author': 'kyles', 'title': 'dune buggy muscle car pass slow loud nearby full engine rev and trail off to right.wav', 'page': 'https://freesound.org/people/kyles/sounds/413905/', 'download': 'https://cdn.freesound.org/previews/413/413905_612689-hq.mp3', 'license': 'CC0-1.0', 'licenseUrl': 'https://creativecommons.org/publicdomain/zero/1.0/', 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'note': 'Derived from the public HQ MP3 preview. RPM bands are playback tuning, not measured RPM of the original vehicle.', 'derived': receipts}
(target/'EXHAUST-SOURCE.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf8')
print(json.dumps(receipt, indent=2))
