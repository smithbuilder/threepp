"""Prepare the Safari-only recorded exhaust voice, without synthesized tones.

Uses the already licensed, locally retained CC0 recording. Original buggy
assets are never rewritten. An optional CSV containing exact C++ band states
produces review previews; the mixer performs no independent powertrain model.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, subprocess, wave
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RATE=48000
SOURCE_SHA='d94cf3da98ceb2c2890cb44a9a81fac23cfba2e6840cba282065b10e378479fb'
ORIGINALS={
 'idle':'3f45e1feb7b9e4fe88400ed06b46bb557fc95edb3296633e4f3c4595e9938fa2',
 'mid':'b0268a5545bdf08376e310a7545fbe36a139401435a295b15d014a3b4984b1e9',
 'high':'7f8a92833da55a558e92fc1a7c16b674ac3e950382ebfa2946aff2db1aac8391'}
FILTER='highpass=f=42:p=2,highpass=f=42:p=2,bass=g=3:f=110:w=0.7,equalizer=f=430:t=q:w=0.7:g=-1,equalizer=f=850:t=q:w=0.6:g=3,treble=g=-1:f=1800,lowpass=f=4600:p=2'
# Stable lower-speed pressure pulses for idle, a more textured recorded pull
# for midrange, and the actual louder recorded pass for the upper register.
# This retains combustion rasp instead of turning the whole voice into bass.
BANDS=[('idle',28.1,2.4,.40,1050,-14.0),('mid',5.0,2.4,.72,2800,-12.5),('high',22.0,2.4,1.38,4800,-13.5)]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args,data=None):
 r=subprocess.run(args,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-1800:])
 return r
def decode(p):
 return np.frombuffer(run(['ffmpeg','-nostdin','-v','error','-threads','2','-i',str(p),'-f','f32le','-ac','1','-ar',str(RATE),'-']).stdout,dtype='<f4').astype(float)
def write(p,x,stereo=False):
 x=np.asarray(x);assert np.isfinite(x).all() and np.max(np.abs(x))<1
 pcm=np.rint(x*32767).astype('<i2')
 with wave.open(str(p),'wb') as w:
  w.setnchannels(2 if stereo else 1);w.setsampwidth(2);w.setframerate(RATE)
  w.writeframes(np.repeat(pcm[:,None],2,axis=1).tobytes() if stereo else pcm.tobytes())
def stats(x):
 x=np.asarray(x,dtype=float);n=len(x);freq=np.fft.rfftfreq(n,1/RATE);power=np.abs(np.fft.rfft(x*np.hanning(n)))**2;total=power.sum()
 return dict(seconds=n/RATE,rmsDbFS=20*math.log10(float(np.sqrt(np.mean(x*x)))),peakDbFS=20*math.log10(float(np.max(np.abs(x)))),dc=float(np.mean(x)),
  powerCentroidHz=float((freq*power).sum()/total),powerFractions={f'{a}-{b}Hz':float(power[(freq>=a)&(freq<b)].sum()/total) for a,b in [(0,35),(35,150),(150,500),(500,2000),(2000,12000)]},
  loopSeamJump=float(abs(x[0]-x[-1])),adjacentJump99=float(np.quantile(np.abs(np.diff(x)),.99)))
def level(p):
 t=run(['ffmpeg','-nostdin','-hide_banner','-threads','2','-i',str(p),'-vn','-af','ebur128=peak=true','-f','null','-']).stderr.decode(errors='replace')
 return dict(lufs=float(re.findall(r'I:\s*(-?[\d.]+)\s*LUFS',t)[-1]),truePeakDb=float(re.findall(r'Peak:\s*(-?[\d.]+)\s*dBFS',t)[-1]))
def prepare(source,output):
 assert sha(source)==SOURCE_SHA,'Unexpected source recording; obtain a separate license/provenance review.'
 for name,digest in ORIGINALS.items():assert sha(output/f'cinder_exhaust_{name}.wav')==digest,'Original buggy audio changed'
 raw=decode(source);items=[]
 for name,start,duration,pitch,band_rpm,target_rms in BANDS:
  x=raw[int(start*RATE):int((start+duration)*RATE)]
  # Preserve the recorded pressure waveform and its texture at a lower voice.
  # No oscillator, noise generator, subharmonic or unrelated rumble is layered.
  x=np.interp(np.arange(0,len(x)-1,pitch),np.arange(len(x)),x);x-=x.mean()
  x=np.frombuffer(run(['ffmpeg','-nostdin','-v','error','-threads','2','-filter_threads','1','-f','f32le','-ar',str(RATE),'-ac','1','-i','pipe:0','-af',FILTER,'-f','f32le','-'],x.astype('<f4').tobytes()).stdout,dtype='<f4').astype(float)
  # Modestly remove microphone pass-by level variation over 250 ms; retain
  # individual combustion texture and avoid a repeating loud/quiet loop swell.
  window=int(.25*RATE);padded=np.pad(x*x,(window//2,window-window//2),mode='reflect');cumulative=np.r_[0,np.cumsum(padded)]
  envelope=np.sqrt(np.maximum((cumulative[window:window+len(x)]-cumulative[:len(x)])/window,1e-10))
  x*=np.clip((np.median(envelope)/envelope)**.35,.80,1.30)
  fade=int(.24*RATE);u=np.linspace(0,math.pi/2,fade)
  x=np.r_[x[fade:-fade],x[-fade:]*np.cos(u)+x[:fade]*np.sin(u)];x-=x.mean()
  scale=min(10**(target_rms/20)/np.sqrt(np.mean(x*x)),10**(-5/20)/np.max(np.abs(x)));x*=scale
  p=output/f'safari_exhaust_{name}.wav';write(p,x);s=stats(decode(p))
  assert s['loopSeamJump']<s['adjacentJump99'] and s['peakDbFS']<=-4.99
  items.append(dict(file=p.name,sha256=sha(p),sourceStartSeconds=start,sourceDurationSeconds=duration,offlinePlaybackRatio=pitch,playbackBandRpm=band_rpm,statistics=s))
 for name,digest in ORIGINALS.items():assert sha(output/f'cinder_exhaust_{name}.wav')==digest
 receipt=dict(version=1,author='kyles',title='dune buggy muscle car pass slow loud nearby full engine rev and trail off to right.wav',page='https://freesound.org/people/kyles/sounds/413905/',license='CC0-1.0',licenseUrl='https://creativecommons.org/publicdomain/zero/1.0/',sourceSha256=SOURCE_SHA,
  sourceNote='Existing public HQ MP3 preview retained locally. Bands/gearing are original fictional-car tuning, not measured source RPM or a matched Porsche flat-six recording.',
  method='Recorded waveform only; offline lower register, restrained EQ, mild 250ms pass-by envelope reduction, 240ms equal-power circular join, DC removal and bounded normalization. No oscillator/synthesized bass/subharmonic/noise layer.',
  filter=FILTER,originalBuggyHashes=ORIGINALS,derived=items)
 (output/'SAFARI-EXHAUST-SOURCE.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
def preview(csv_path,folder):
 rows=list(csv.DictReader(csv_path.open(newline='')));duration=float(rows[-1]['time'])+1/30
 times=np.arange(round(duration*RATE))/RATE;frame_time=np.array([float(r['time']) for r in rows]);report={};mixes={}
 for prefix,asset in [('old','cinder'),('new','safari')]:
  mix=np.zeros(len(times))
  for i,name in enumerate(['idle','mid','high']):
   x=decode(ROOT/'showcase/assets'/f'{asset}_exhaust_{name}.wav');pitch=np.interp(times,frame_time,[float(r[f'{prefix}Pitch{i}']) for r in rows]);gain=np.interp(times,frame_time,[float(r[f'{prefix}Gain{i}']) for r in rows])
   phase=np.mod(np.cumsum(pitch)-pitch,len(x));left=np.floor(phase).astype(int);fraction=phase-left
   mix+=(x[left]*(1-fraction)+x[(left+1)%len(x)]*fraction)*gain
  fade=int(.025*RATE);mix[:fade]*=np.linspace(0,1,fade);mix[-fade:]*=np.linspace(1,0,fade)
  p=folder/f'{prefix}-raw.wav';write(p,mix,True);measurement=level(p);g=min(-18-measurement['lufs'],-2.5-measurement['truePeakDb']);mix*=10**(g/20)
  p=folder/f'{prefix}-preview.wav';write(p,mix,True);measurement=level(p);s=stats(mix)
  report[prefix]=dict(file=str(p),sha256=sha(p),normalizingGainDb=g,loudness=measurement,statistics=s);mixes[prefix]=mix
 # Equal-loudness A/B with a small silence: baseline then new, never overlaid.
 ab=np.r_[mixes['old'],np.zeros(int(.5*RATE)),mixes['new']];write(folder/'Safari-Exhaust-Before-After.wav',ab,True)
 (folder/'preview-report.json').write_text(json.dumps(dict(sourceCSV=str(csv_path),sourceCSVSha256=sha(csv_path),scope='CPU-generated review, exact C++ band controls; no physical audio output or subjective listening acceptance',profiles=report),indent=2)+'\n')
 return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'build/audio-source/buggy-kyles-413905.mp3');p.add_argument('--csv',type=Path);p.add_argument('--out',type=Path,default=ROOT/'build/safari-audio-iteration');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 receipt=prepare(a.source,ROOT/'showcase/assets');print(json.dumps(dict(assets=[x['file'] for x in receipt['derived']],preview=preview(a.csv,a.out) if a.csv else None),indent=2))
if __name__=='__main__':main()
