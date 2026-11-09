"""Original, quiet placeholder cues. Gain is measured by ffmpeg loudnorm."""
from pathlib import Path
import math,random,struct,wave,subprocess,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Unity/Assets/Resources/Cinder/Audio';OUT.mkdir(parents=True,exist_ok=True)
work=ROOT/'build/unity-audio';work.mkdir(parents=True,exist_ok=True);rows=[]
for kind,duration,target in [('engine',.20,-30),('pump',.24,-29),('landing',.38,-24),('impact',.25,-25)]:
    rng=random.Random(123);samples=[];rate=48000
    for i in range(int(rate*duration)):
        t=i/rate;fade=min(1,t/.025,(duration-t)/.055);env=max(0,fade)**2
        if kind=='engine':v=.32*math.sin(math.tau*55*t)+.14*math.sin(math.tau*110*t)+.05*math.sin(math.tau*165*t)
        elif kind=='pump':v=.20*math.sin(math.tau*138*t)+.06*math.sin(math.tau*276*t)
        else:v=(.45*math.sin(math.tau*(64-28*t)*t)+.08*rng.uniform(-1,1))*math.exp(-t*15)
        samples.append(int(max(-1,min(1,v*env))*32767))
    raw=work/(kind+'.wav')
    with wave.open(str(raw),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(struct.pack('<'+'h'*len(samples),*samples))
    # Repeat for a valid integrated loudness window, then trim the normalized cue.
    dest=OUT/(kind+'.wav')
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-stream_loop','15','-i',str(raw),'-af',f'loudnorm=I={target}:TP=-6:LRA=5','-t',str(duration),'-ar',str(rate),'-ac','1',str(dest)],check=True)
    result=subprocess.run(['ffmpeg','-hide_banner','-stream_loop','15','-i',str(dest),'-af','loudnorm=print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr
    stats=json.loads(result[result.rfind('{'):result.rfind('}')+1]);rows.append(dict(id=kind,file='Unity/Assets/Resources/Cinder/Audio/'+dest.name,source='tools/unity/make_audio.py',author='SmithBuilder',license='Original synthesized placeholder',date='2026-11-08',integratedLUFS=float(stats['input_i']),truePeakDBTP=float(stats['input_tp']),notes='Measured with repeated cue. Human listening remains UNVERIFIED.'))
(ROOT/'assets/unity/audio-provenance.json').write_text(json.dumps({'cues':rows,'playback':'All cues originate from simulation Events, distance-delayed by listener range /343 m/s'},indent=2)+'\n')
print(json.dumps(rows,indent=2))
