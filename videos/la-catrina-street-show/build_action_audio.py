"""Reconstruct quiet engine/pump sound from CC0 recordings and actual capture telemetry.

No native simulator audio or measured RPM claim. Music remains a separate editable track.
"""
from pathlib import Path
import csv,hashlib,json,subprocess,wave
import numpy as np

ROOT=Path(__file__).resolve().parent;SR=48000;N=48*SR
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=json.loads((ROOT/'native-captures.json').read_text(encoding='utf-8-sig'))
edit=json.loads((ROOT/'edit-manifest.json').read_text())
clips={c['name']:c for c in native['clips']}
enginePath=ROOT/'assets/audio/muscle-engine-idle.wav'
pumpPath=ROOT/'assets/audio/lowrider-hydraulics-source.mp3'
assert sha(enginePath)=='3f45e1feb7b9e4fe88400ed06b46bb557fc95edb3296633e4f3c4595e9938fa2'
assert sha(pumpPath)=='9207c43eb13f97d5356dee3aa52391f68bec40bc66819691c24bfad24cab3dcc'
def decode(p):
    return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-ac','1','-ar',str(SR),'-f','f32le','pipe:1']),dtype=np.float32).astype(np.float64)
engine=decode(enginePath);pumps=decode(pumpPath)
audio=np.zeros((N,2),np.float64);events=[]
# The existing engine loop already has a160ms circular seam. No retuning to fictitious RPM.
bed=np.resize(engine,N)
frameGain=np.full(1440,.055)
for scene in edit['scenes']:
    c=clips[scene['id']];session=Path(c['session'])
    result=json.loads((session/'result.json').read_text(encoding='utf-8-sig'))
    rows=list(csv.DictReader((session/'drive.json.csv').open(newline='')))
    warmup=result['warmupFrames'];rows=rows[warmup:warmup+c['frames']]
    assert len(rows)==c['frames']
    start=round(scene['start']*30)
    throttle=np.array([float(r['throttle']) for r in rows]);speed=np.array([abs(float(r['speed'])) for r in rows])
    frameGain[start:start+len(rows)]=.045+.025*np.clip(throttle,0,1)+.008*np.clip(speed/2,0,1)
    strokes=np.array([[float(r[k]) for k in ('flStroke','frStroke','rlStroke','rrStroke')] for r in rows])
    change=np.maximum(0,np.diff(strokes,axis=0,prepend=strokes[:1])).sum(axis=1)
    rising=change>.006
    beginnings=np.where(rising & ~np.r_[False,rising[:-1]])[0]
    for local in beginnings:
        end=local+1
        while end<len(rising) and rising[end]:end+=1
        duration=max(.16,min(.65,(end-local)/30+.07))
        # Alternate three real pump sections from the documented lowrider recording.
        sourceStart=(39.04,41.08,50.53)[len(events)%3]
        sample=pumps[round(sourceStart*SR):round((sourceStart+duration)*SR)].copy()
        if not len(sample):continue
        sample*=.22/max(float(abs(sample).max()),.01)
        fade=min(round(.018*SR),len(sample)//2);sample[:fade]*=np.linspace(0,1,fade);sample[-fade:]*=np.linspace(1,0,fade)
        at=round((scene['start']+(local+1)/30)*SR);stop=min(N,at+len(sample));sample=sample[:stop-at]
        audio[at:stop,0]+=sample*.72;audio[at:stop,1]+=sample*.70
        events.append({'scene':scene['id'],'nativeFrame':warmup+int(local),'filmTime':scene['start']+(int(local)+1)/30,'duration':len(sample)/SR,'sourceStart':sourceStart,'cause':'Positive change in actual hydraulic extension; one-frame audio offset'})
gain=np.interp(np.arange(N)/SR,np.arange(1440)/30,frameGain)
audio[:,0]+=bed*gain*.72;audio[:,1]+=bed*gain*.70
edge=np.minimum(1,np.arange(N)/(SR*.3))*np.minimum(1,(N-1-np.arange(N))/(SR*1.0));audio*=np.maximum(edge,0)[:,None]
assert np.max(abs(audio))<.8
path=ROOT/'assets/audio/catrina-action.wav'
with wave.open(str(path),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes(np.int16(np.clip(audio,-1,1)*32767).tobytes())
receipt={'status':'PASS','durationSeconds':48,'sampleRate':SR,'channels':2,'sha256':sha(path),'peakLinear':float(abs(audio).max()),'recordings':[{'path':str(enginePath),'sha256':sha(enginePath),'credit':'kyles / Freesound413905 / CC0'},{'path':str(pumpPath),'sha256':sha(pumpPath),'credit':'nick121087 / Freesound342463 / CC0'}],'events':events,'telemetryBinding':'native-captures.json and each drive.json.csv, dropping the declared warmup frames','truth':'Editorial reconstruction from actual recordings, not simulator-captured sound or measured vehicle RPM. No new synthesized machinery.','listeningReview':False}
(ROOT/'assets/audio/ACTION-PROVENANCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':'PASS','events':len(events),'durationSeconds':48,'sha256':sha(path)},indent=2))
