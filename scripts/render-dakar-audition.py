"""Mix the signed game's CPU audition controls, without an audio endpoint."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import wave
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RATE=48000


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('controls',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    rows=list(csv.DictReader(a.controls.open()))
    native='time' not in rows[0]
    # Native simulation time freezes on the results screen; audio still has a
    # frame-clock duration. Captures are explicitly fixed at30frames/second.
    times=np.arange(len(rows))/30 if native else np.array([float(r['time']) for r in rows])
    t=np.arange(round((times[-1]+1/30)*RATE))/RATE;mix=np.zeros(len(t));sources=[]
    for i,name in enumerate(['idle','mid','high']):
        path=ROOT/'showcase/assets'/f'safari_exhaust_{name}.wav'
        with wave.open(str(path),'rb') as w:
            assert w.getframerate()==RATE and w.getnchannels()==1 and w.getsampwidth()==2
            x=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
        pitch=np.interp(t,times,[float(r[f'exhaustPitch{i}']) for r in rows]);gain=np.interp(t,times,[float(r[f'exhaustGain{i}']) for r in rows])
        assert np.isfinite(pitch).all() and np.min(pitch)>0 and np.isfinite(gain).all() and np.min(gain)>=0
        phase=np.mod(np.cumsum(pitch)-pitch,len(x));index=np.floor(phase).astype(int);fraction=phase-index
        mix+=(x[index]*(1-fraction)+x[(index+1)%len(x)]*fraction)*gain
        sources.append(dict(file=path.name,sha256=sha(path)))
    fade=round(.025*RATE);mix[:fade]*=np.linspace(0,1,fade);mix[-fade:]*=np.linspace(1,0,fade)
    assert np.isfinite(mix).all() and np.max(abs(mix))<1
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(a.output),'wb') as w:
        w.setparams((2,2,RATE,0,'NONE','not compressed'))
        pcm=np.rint(mix*32767).astype('<i2');w.writeframes(np.repeat(pcm[:,None],2,axis=1).tobytes())
    measurement=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-threads','2','-i',str(a.output),'-filter_threads','1','-af','ebur128=peak=true','-f','null','-'],capture_output=True,check=True).stderr.decode(errors='replace').rsplit('Summary:',1)[-1]
    scope=('Reconstructed exhaust from guarded native frame controls before listener master volume; not endpoint recording.' if native else
           'CPU audition of runtime band controls before the listener master volume; prescribed pedal/speed states, not a native driven lap or endpoint recording.')
    receipt=dict(scope=scope,
        auditionMasterVolume=1.0,runtimeListenerMasterVolume=.75,
        controls=str(a.controls),controlsSha256=sha(a.controls),sources=sources,outputSha256=sha(a.output),
        seconds=len(mix)/RATE,samplePeakDbFS=float(20*np.log10(np.max(abs(mix)))),clippedSamples=int(np.sum(abs(mix)>=1)),measurement=measurement)
    a.output.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
