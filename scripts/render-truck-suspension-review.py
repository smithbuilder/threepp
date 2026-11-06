"""Assemble verified native truck shots. No generated or interpolated picture."""
import argparse, csv, hashlib, importlib.util, json, math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
RATE = 48000
spec = importlib.util.spec_from_file_location('native_review', Path(__file__).with_name('render-safari-review.py'))
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
run, measure, sha = helpers.run, helpers.measure, helpers.sha

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def engine_audio(rows, sources):
    """Temporary generic engine + tyre/impact sound driven by native logs."""
    n = len(rows)
    field = lambda name: np.array([float(row[name]) for row in rows])
    speed, throttle, scale = abs(field('speed')), field('throttle'), field('playbackScale')
    rpm, rpm_log, load_log, load = 950., [], [], 0.
    for v, gas, playback in zip(speed, throttle, scale):
        gear = 1 if v < 8 else 2 if v < 17 else 3
        target = min(5600., 950. + v * (320, 180, 125)[gear-1] + gas*180)
        rpm += (target-rpm)*(1-math.exp(-8*playback/30))
        load += (gas-load)*(1-math.exp(-5*playback/30))
        rpm_log.append(rpm); load_log.append(load)
    rpm, load = np.array(rpm_log), np.array(load_log)
    a, b = np.clip((rpm-1600)/1900,0,1), np.clip((rpm-3400)/2100,0,1)
    weights = [np.sqrt(1-a), np.sqrt(a*(1-b)), np.sqrt(b)]
    times = np.arange(n*1600)/RATE; frame_times=np.arange(n)/30
    voice=np.zeros(len(times))
    for i,sample in enumerate(sources):
        pitch = np.clip(rpm/(2600,3900,5600)[i], .48 if i==0 else .72, 1.12 if i==0 else 1.3)*np.sqrt(scale)
        gain = weights[i]*(.22+.3*load)
        pitch, gain = np.interp(times,frame_times,pitch), np.interp(times,frame_times,gain)
        phase=np.mod(np.cumsum(pitch)-pitch+.173*RATE,len(sample)); index=phase.astype(int); fraction=phase-index
        voice+=(sample[index]*(1-fraction)+sample[(index+1)%len(sample)]*fraction)*gain
    loads=np.array([[float(r[k+'Load']) for k in ('fl','fr','rl','rr')] for r in rows]).sum(axis=1)
    rng=np.random.default_rng(427)
    road=sosfilt(butter(2,900,fs=RATE,output='sos'),rng.normal(0,1,len(times)))
    road*=np.interp(times,frame_times,np.clip(speed/12,0,1)*np.clip(loads/(2480*9.81),0,1))*.016
    voice+=road
    # Small original procedural landing thumps; timing comes from supporting load.
    for i in range(1,n):
        if float(rows[i-1]['contacts'])==0 and float(rows[i]['contacts'])>=2:
            count=min(int(.18*RATE),len(voice)-i*1600); t=np.arange(count)/RATE
            voice[i*1600:i*1600+count]+=.05*np.sin(2*np.pi*52*t)*np.exp(-t*25)
    camera=np.array([[float(r['camera'+k]) for k in 'XYZ'] for r in rows])
    origin=np.array([[float(r[k]) for k in 'xyz'] for r in rows])
    distance=np.linalg.norm(camera-origin,axis=1)
    gain=.9/(1+(distance/12)**2)
    if rows[0]['view']=='6':
        voice=sosfilt(butter(2,1800,fs=RATE,output='sos'),voice);gain*=.8
    voice*=np.interp(times,frame_times,gain)
    fade=min(1600,len(voice)//2);voice[:fade]*=np.linspace(0,1,fade);voice[-fade:]*=np.linspace(1,0,fade)
    return np.column_stack((voice,voice))*.70710678

def main():
    parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    output=args.output.resolve();assert not output.exists(),'Preserve previous videos'
    proof=output.parent/'proof';proof.mkdir(parents=True,exist_ok=True)
    clips=load(args.manifest); records=[]; encoded=[]; audio=[]; samples=[]; identities=set(); movie_frame=0
    sources=[]; audio_sources=[]
    for band in ('idle','mid','high'):
        path=ROOT/'showcase/assets'/f'cinder_exhaust_{band}.wav'
        with wave.open(str(path),'rb') as wav:
            assert (wav.getframerate(),wav.getnchannels(),wav.getsampwidth())==(RATE,1,2)
            sources.append(np.frombuffer(wav.readframes(wav.getnframes()),'<i2').astype(float)/32768)
        audio_sources.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path)})
    for index, clip in enumerate(clips):
        session=ROOT/'build/sessions'/clip['session'];result=load(session/'result.json')
        assert result['example']=='suspension_playground' and result['vehicle']=='baja' and result['exitCode']==0 and result['sequence']
        assert result['renderWidth']==960 and result['renderHeight']==600 and result['captureScale']==1
        assert (session/'stderr.log').stat().st_size==0
        identities.add((result['binarySha256'], result['playgroundAssetSha256']['baja-427.glb']))
        csv_path=session/'drive.json.csv';trace=list(csv.DictReader(csv_path.open(newline='')))
        assert len(trace)==result['warmupFrames']+result['requestedFrames']
        for row in trace: assert all(math.isfinite(float(v)) for v in row.values())
        start,count=clip['start'],clip['frames'];assert start>=0 and start+count<=result['requestedFrames']
        rows=trace[result['warmupFrames']+start:result['warmupFrames']+start+count]
        hashes=[]
        for frame in range(start,start+count):
            path=session/'frames'/f'frame_{frame:05d}.png'
            with Image.open(path) as im:assert im.size==(960,600)
            hashes.append(sha(path))
        part=proof/f'{index:02d}.mp4'
        run(['ffmpeg','-nostdin','-v','error','-y','-framerate','30','-start_number',str(start),'-i',str(session/'frames/frame_%05d.png'),'-frames:v',str(count),'-an','-c:v','libx264','-threads','2','-filter_threads','1','-preset','medium','-crf','17','-vf','scale=iw:ih:out_color_matrix=bt709:out_range=tv,format=yuv420p','-colorspace','bt709',str(part)],proof/f'{index:02d}-encode.log')
        encoded.append(part);audio.append(engine_audio(rows,sources))
        records.append({**clip,'resultSha256':sha(session/'result.json'),'traceSha256':sha(csv_path),'frameHashes':hashes,'firstPhysicsTime':float(rows[0]['t']),'lastPhysicsTime':float(rows[-1]['t']),'maxWheelTravelRange':max(max(float(r[k+'Travel']) for r in rows)-min(float(r[k+'Travel']) for r in rows) for k in ('fl','fr','rl','rr'))})
        for f in sorted(set([0,count//2,count-1])):
            samples.append({'movieFrame':movie_frame+f,'path':str((session/'frames'/f'frame_{start+f:05d}.png').relative_to(ROOT)),'label':clip['label']})
        movie_frame+=count
    assert len(identities)==1,'Do not mix model/binary revisions'
    # Alternate front/rear service views must show the same physical replay.
    service=[c for c in clips if c.get('match')=='articulation']
    if len(service)==2:
        a,b=[list(csv.DictReader((ROOT/'build/sessions'/c['session']/'drive.json.csv').open(newline=''))) for c in service]
        fields=[k for k in a[0] if not k.startswith('camera') and k!='view']
        assert len(a)==len(b) and all(all(x[k]==y[k] for k in fields) for x,y in zip(a,b))
    jumps=[c for c in clips if c.get('match')=='jump']
    if len(jumps)==2:
        a,b=[list(csv.DictReader((ROOT/'build/sessions'/c['session']/'drive.json.csv').open(newline=''))) for c in jumps]
        fields=[k for k in a[0] if not k.startswith('camera') and k!='view']
        assert len(a)==len(b) and all(all(x[k]==y[k] for k in fields) for x,y in zip(a,b))
    listing=proof/'concat.txt';listing.write_text(''.join(f"file '{p.name}'\n" for p in encoded))
    picture=proof/'native-picture.mp4';run(['ffmpeg','-nostdin','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(picture)],proof/'concat.log')
    mix=np.concatenate(audio);assert np.isfinite(mix).all();mix*=min(1,.85/max(abs(mix).max(),1e-9))
    sound=proof/'engine-and-tyres.wav'
    def write_audio():
        assert np.max(abs(mix))<1
        with wave.open(str(sound),'wb') as w:w.setparams((2,2,RATE,0,'NONE','not compressed'));w.writeframes(np.rint(mix*32767).astype('<i2').tobytes())
    write_audio();metrics=measure(sound);gain=min(-18-metrics['lufs'],-3-metrics['truePeakDb']);mix*=10**(gain/20);write_audio()
    run(['ffmpeg','-nostdin','-v','error','-y','-i',str(picture),'-i',str(sound),'-c:v','copy','-c:a','aac','-threads','2','-b:a','192k','-movflags','+faststart','-shortest',str(output)],proof/'mux.log')
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]).stdout)
    v=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert v['width']==960 and v['height']==600 and v['avg_frame_rate']=='30/1' and int(v['nb_frames'])==movie_frame
    assert abs(float(probe['format']['duration'])-movie_frame/30)<.04
    decode=run(['ffmpeg','-nostdin','-v','error','-threads','2','-i',str(output),'-f','null','-'],proof/'decode.log');assert not decode.stderr
    metrics=measure(output);assert metrics['truePeakDb']<0
    receipt={'status':'PASS','output':str(output.relative_to(ROOT)),'sha256':sha(output),'bytes':output.stat().st_size,'frames':movie_frame,'seconds':movie_frame/30,'binarySha256':next(iter(identities))[0],'modelSha256':next(iter(identities))[1],'fullDecodePassed':True,'audioMeasurement':metrics,'clips':records,'audioSources':audio_sources,'audioCredits':load(ROOT/'showcase/assets/EXHAUST-SOURCE.json'),'audio':'Temporary reconstructed generic engine, tyres and procedural landing thumps driven by native logs; not endpoint audio.','picture':'Actual native960x600/30fps. Half-speed shots integrate the same240Hz physics at half rate; no interpolated frames or authored jump trajectory.','matchedReplayChecks':{'articulation':len(service)==2,'jump':len(jumps)==2},'sourceSamples':samples,'assemblerSha256':sha(Path(__file__))}
    (proof/'probe.json').write_text(json.dumps(probe,indent=2)+'\n');(proof/'provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (output.parent/'render-result.json').write_text(json.dumps({k:v for k,v in receipt.items() if k not in ('clips','audioCredits','sourceSamples')},indent=2)+'\n')
    sheet=Image.new('RGB',(960*2,625*((len(samples)+1)//2)),(18,20,21));draw=ImageDraw.Draw(sheet)
    for i,s in enumerate(samples):
        x=i%2*960;y=i//2*625;sheet.paste(Image.open(ROOT/s['path']).convert('RGB'),(x,y));draw.text((x+10,y+603),f"{s['movieFrame']/30:.2f}s / {s['label']}",fill='white')
    sheet.save(output.parent/'native-review-sheet.jpg',quality=88)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('clips','audioCredits','sourceSamples','audioSources')},indent=2))

if __name__=='__main__':main()
