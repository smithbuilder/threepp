"""Original deterministic instrumental bed. No provider or recorded engine audio."""
from pathlib import Path
import hashlib,json,math,subprocess,wave
import numpy as np

ROOT=Path(__file__).resolve().parent
SR=48000;DURATION=45;N=SR*DURATION
rng=np.random.default_rng(27041984)
audio=np.zeros((N,2),np.float64)

def add(t,sound,level=1,pan=0):
    start=round(t*SR);sound=np.asarray(sound)*level
    end=min(N,start+len(sound))
    if end<=start:return
    sound=sound[:end-start]
    audio[start:end,0]+=sound*math.sqrt((1-pan)/2)
    audio[start:end,1]+=sound*math.sqrt((1+pan)/2)

def note(midi,duration,kind='pluck'):
    t=np.arange(round(duration*SR))/SR;f=440*2**((midi-69)/12)
    if kind=='bass':
        env=np.minimum(t/.008,1)*np.exp(-t*5.5)
        return (np.sin(2*np.pi*f*t)+.20*np.sin(4*np.pi*f*t))*env
    if kind=='pad':
        env=np.minimum(t/.3,1)*np.minimum((duration-t)/.4,1)
        return (np.sin(2*np.pi*f*t)+.14*np.sin(2*np.pi*f*2.002*t))*np.maximum(0,env)
    env=np.minimum(t/.004,1)*np.exp(-t*8)
    return (np.sin(2*np.pi*f*t)+.27*np.sin(2*np.pi*f*2*t)+.08*np.sin(2*np.pi*f*3*t))*env

# 120 BPM, restrained percussion; section changes match the exact film edits.
chords=[(40,52,55,59),(36,48,52,55),(43,50,55,59),(38,50,54,57)]
for beat in range(88):
    at=beat*.5
    if at<43:
        t=np.arange(int(.22*SR))/SR
        freq=46+76*np.exp(-t*25);phase=2*np.pi*np.cumsum(freq)/SR
        kick=np.sin(phase)*np.exp(-t*20)+rng.normal(0,1,len(t))*np.exp(-t*180)*.07
        add(at,kick,.19 if at>8.5 else .14)
    if beat%2==1 and 8.5<=at<42.5:
        t=np.arange(int(.17*SR))/SR;noise=rng.normal(0,1,len(t))
        snare=(noise-.8*np.roll(noise,1))*np.exp(-t*31)+.25*np.sin(2*np.pi*178*t)*np.exp(-t*24)
        add(at,snare,.035,-.05)
    if at<43:
        for off in (0,.25):
            t=np.arange(int(.055*SR))/SR;noise=rng.normal(0,1,len(t));noise=noise-np.roll(noise,1)
            add(at+off,noise*np.exp(-t*80),.011 if off else .015, .42 if off else -.42)
    chord=chords[(beat//8)%len(chords)]
    if at>=1 and at<43:
        midi=chord[0]+(12 if beat%4==3 else 0)
        add(at,note(midi,.43,'bass'),.155)
    if beat%4==0 and at<42:
        for i,midi in enumerate(chord[1:]):add(at,note(midi,2.1,'pad'),.026,(i-1)*.50)
    if 9<=at<43 and beat%2==0:
        pattern=[0,2,1,2,0,1,2,1];midi=chord[1+pattern[(beat//2)%8]]+12
        add(at+.25,note(midi,.75),.052,(-.25 if beat%4 else .25))
        add(at+.5,note(midi,.60),.013,(.25 if beat%4 else -.25))

# Deliberate final chord and tail, no hard stop or artificial vehicle sound.
for midi,pan in ((52,-.3),(55,0),(59,.3),(64,.12)):add(43.0,note(midi,2.0,'pad'),.048,pan)
time=np.arange(N)/SR
envelope=np.minimum(1,time/.65)*np.minimum(1,(DURATION-time)/1.45)
audio*=np.maximum(envelope,0)[:,None]
audio=np.tanh(audio*1.15)
audio*=.72/max(float(abs(audio).max()),.01)
out=ROOT/'assets/audio';out.mkdir(parents=True,exist_ok=True)
raw=ROOT/'proof/music-original-raw.wav';raw.parent.mkdir(parents=True,exist_ok=True)
with wave.open(str(raw),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes(np.int16(np.clip(audio,-1,1)*32767).tobytes())
final=out/'switchback-original.wav'
cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(raw),'-af','loudnorm=I=-18:TP=-2.5:LRA=8','-ar',str(SR),'-c:a','pcm_s16le',str(final)]
subprocess.run(cmd,check=True)
receipt={'title':'Switchback / Sunset Pulse','type':'original locally authored instrumental','durationSeconds':DURATION,'sampleRate':SR,'channels':2,'tempoBpm':120,'seed':27041984,'source':'make_music.py','externalSamples':False,'engineAudio':False,'license':'Original generated composition and synthesis code for this project; no external samples or third-party music.','sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'normalization':'EBU R128 loudnorm target -18 LUFS, true peak -2.5 dBTP, LRA8'}
(out/'MUSIC-PROVENANCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
