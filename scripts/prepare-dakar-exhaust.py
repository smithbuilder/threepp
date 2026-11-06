"""Temporary personal-project voice from Porsche's recorded 911 Dakar.

This is a local prototype derivative of copyrighted press footage, not a CC0
library asset. No narration, logo sting, oscillator or invented bass is added.
Nominal RPM is a firing-harmonic estimate, not recorded tachometer telemetry.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import subprocess
import wave
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RATE=48000
SOURCE=ROOT/'build/fidelity-v1/audio-review/dakar-driving-15-60.m4a'
# Local snippet time is official footage time minus15 seconds.
BANDS=[('idle',24.6,1.2,900,-17),('mid',8.1,.7,2200,-16),('high',7.1,.7,2800,-16)]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def run(args,data=None):
    r=subprocess.run(args,input=data,capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-1600:])
    return r.stdout


def decode(p):
    return np.frombuffer(run(['ffmpeg','-nostdin','-v','error','-threads','2','-i',str(p),
        '-ac','1','-ar',str(RATE),'-f','f32le','-']),dtype='<f4').astype(float)


def write(p,x):
    assert np.isfinite(x).all() and np.max(np.abs(x))<1
    with wave.open(str(p),'wb') as w:
        w.setparams((1,2,RATE,0,'NONE','not compressed'))
        w.writeframes(np.rint(x*32767).astype('<i2').tobytes())


def stats(x):
    return dict(seconds=len(x)/RATE,rmsDbFS=20*math.log10(np.sqrt(np.mean(x*x))),
        peakDbFS=20*math.log10(np.max(np.abs(x))),dc=float(x.mean()),
        loopSeamJump=float(abs(x[-1]-x[0])),
        adjacentJump99=float(np.quantile(abs(np.diff(x)),.99)))


def prepare():
    raw=decode(SOURCE);items=[]
    # Keep the actual pressure wave and upper harmonics. No extreme slowdown,
    # music, synthetic subharmonic or unrelated rumble is used.
    for name,start,duration,rpm,target in BANDS:
        x=raw[round(start*RATE):round((start+duration)*RATE)]
        filt='highpass=f=32:p=2,lowpass=f=6500:p=2'
        # Requested low-RPM direction: more pressure below120Hz, less distant
        # microphone hiss. Keep original timing/combustion pulses unchanged.
        if name=='idle':filt='highpass=f=32:p=2,bass=g=4:f=95:w=.7,equalizer=f=900:t=q:w=.7:g=-1.5,lowpass=f=3500:p=2'
        elif name=='mid':filt='highpass=f=32:p=2,bass=g=1.5:f=105:w=.7,lowpass=f=6500:p=2'
        x=np.frombuffer(run(['ffmpeg','-nostdin','-v','error','-threads','2',
            '-filter_threads','1','-f','f32le','-ar',str(RATE),'-ac','1','-i','pipe:0',
            '-af',filt,'-f','f32le','-'],x.astype('<f4').tobytes()),dtype='<f4').astype(float)
        x-=x.mean()
        # Find a close waveform phase near the end. A short circular overlap
        # then joins recorded neighbouring cycles, rather than a broad smear.
        fade=round(.055*RATE);head=x[:fade]
        candidates=range(len(x)-round(.11*RATE)-fade,len(x)-fade,8)
        end=min(candidates,key=lambda at:float(np.mean((x[at:at+fade]-head)**2)))
        x=x[:end+fade]
        # These are phase-matched, correlated engine cycles: complementary
        # amplitude weights avoid the periodic +3dB swell of equal-power fades.
        weight=.5-.5*np.cos(np.linspace(0,math.pi,fade))
        x=np.r_[x[fade:-fade],x[-fade:]*(1-weight)+x[:fade]*weight]
        x-=x.mean();x*=min(10**(target/20)/np.sqrt(np.mean(x*x)),10**(-5/20)/max(abs(x)))
        p=ROOT/'showcase/assets'/f'safari_exhaust_{name}.wav';write(p,x)
        measured=stats(decode(p))
        assert measured['loopSeamJump']<=measured['adjacentJump99'] and measured['peakDbFS']< -4.99
        items.append(dict(file=p.name,sha256=sha(p),officialSourceStartSeconds=start+15,
            sourceDurationSeconds=duration,nominalBandRpm=rpm,
            calibration='Approximate six-cylinder firing-harmonic estimate; Doppler/load uncertain.',
            processing=filt+'; phase-selected55ms complementary raised-cosine circular join; DC removal; peak<=-5dBFS',
            statistics=measured))
    receipt=dict(version=2,source='Porsche AG:911 Dakar in Dubai, driving footage',
        page='https://newstv.porsche.com/en/article/229332.html',
        download='https://newstv.porsche.com/porschevideos/newstv.porsche.com_229332_en.mp4',
        sourceSnippet=str(SOURCE.relative_to(ROOT)),sourceSnippetSha256=sha(SOURCE),
        sourceSnippetOfficialStartSeconds=15,license='Copyright Porsche AG; temporary personal-project sample requested by project owner; no redistribution license established.',
        portableLibrary=False,notes=[
            'Low band is recorded low-energy coast adapted as provisional idle; no stationary idle take was established.',
            'No genuine steady highRPM take was found; upper register is playback of recorded loaded Dakar pressure waves.',
            'Driving snippet had no linguistic words in CPUWhisper screening. This is not subjective listening acceptance.',
            'Rejected walkaround narration and studio logo sting were not used.',
            'Original buggy audio and previous Safari samples remain preserved.'],derived=items)
    receipt['userDirection']='Deeper at lowRPM:4dB/95Hz idle shelf with -17dBFS RMS target constrained by -5dBFS peak;1.5dB/105Hz mid shelf. No playback slowdown or synthetic bass.'
    (ROOT/'showcase/assets/SAFARI-EXHAUST-SOURCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':prepare()
