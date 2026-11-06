"""Assemble two supervised, continuous native race takes and logged exhaust.

CPU only. No engine launch, image generation, resizing or frame interpolation.
Audio is reconstructed from each car's real runtime band controls, not captured
from an audio endpoint. The same fixed 30 Hz picture clock drives both voices.
"""
import argparse,csv,hashlib,json,subprocess,wave,importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
_spec=importlib.util.spec_from_file_location('native_review_helpers',Path(__file__).with_name('render-safari-review.py'))
_helpers=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_helpers)
measure,run,sha=_helpers.measure,_helpers.run,_helpers.sha

ROOT=Path(__file__).resolve().parents[1]
RATE=48000

def write_audio(path,mix):
    assert np.isfinite(mix).all() and np.max(abs(mix))<1
    with wave.open(str(path),'wb') as w:
        w.setparams((2,2,RATE,0,'NONE','not compressed'))
        w.writeframes(np.rint(mix*32767).astype('<i2').tobytes())

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('first');ap.add_argument('second');ap.add_argument('output',type=Path);a=ap.parse_args()
    output=a.output.resolve();assert not output.exists(),'Preserve previous review movies'
    proof=output.parent/(output.stem+'-proof');proof.mkdir(parents=True,exist_ok=True)
    clips=[];records=[];previous=[];offset=0;rows=[];binary=None;asset=None;hasTruck=None;truckAsset=None
    for i,name in enumerate((a.first,a.second)):
        session=ROOT/'build/sessions'/name
        result=json.loads((session/'result.json').read_text(encoding='utf-8-sig'))
        assert result['exitCode']==0 and result['reason']=='exited' and result['sequence'] and result['raceOriginalBuggy']
        assert result['captureScale']==1 and result['renderWidth']==960 and result['renderHeight']==600
        assert (session/'stderr.log').stat().st_size==0
        if i==0:
            binary=result['binarySha256'];asset=result['vehicleAssetSha256'];hasTruck=result.get('raceTruck',False);truckAsset=result.get('truckAssetSha256')
        assert result.get('raceTruck',False)==hasTruck and result.get('truckAssetSha256')==truckAsset
        assert result['binarySha256']==binary and result['vehicleAssetSha256']==asset
        state=list(csv.DictReader((session/'frames/race-state.csv').open(newline='')))
        assert len(state)==result['warmupFrames']+result['requestedFrames']
        assert state[:offset]==previous,'Warmup did not reproduce the preceding race exactly'
        paths=sorted((session/'frames').glob('frame_*.png'));assert len(paths)==result['requestedFrames']
        hashes=[]
        for n,path in enumerate(paths):
            assert path.name==f'frame_{n:05d}.png'
            with Image.open(path) as im:assert im.size==(960,600)
            hashes.append(sha(path))
        clip=proof/f'{i:02d}.mp4'
        run(['ffmpeg','-nostdin','-v','error','-y','-framerate','30','-i',str(session/'frames/frame_%05d.png'),
             '-frames:v',str(len(paths)),'-an','-c:v','libx264','-threads','2','-filter_threads','1','-preset','medium','-crf','16',
             '-vf','scale=iw:ih:out_color_matrix=bt709:out_range=tv,format=yuv420p','-colorspace','bt709',str(clip)],proof/f'{i:02d}-encode.log')
        records.append({'session':name,'frames':len(paths),'warmupFrames':result['warmupFrames'],'resultSha256':sha(session/'result.json'),
                        'raceCsvSha256':sha(session/'frames/race-state.csv'),'frameHashes':hashes,'encodedSha256':sha(clip)})
        clips.append(clip);rows+=state[offset:];offset=len(state);previous=state
    assert len(rows)==offset
    for n,row in enumerate(rows):
        assert int(row['frame'])==n
        assert all(np.isfinite(float(v)) for v in row.values())
        assert float(row['envelopeGap'])>0,'Conservative vehicle envelopes intersect'
        if hasTruck:assert min(float(row[k]) for k in ('safariTruckGap','originalTruckGap'))>0,'Truck overlaps another vehicle'
        for prefix in (('safari','original','truck') if hasTruck else ('safari','original')):
            assert abs(float(row[prefix+'ScreenX']))<.8 and abs(float(row[prefix+'ScreenY']))<.7
    assert rows[-1]['safariFinished']==rows[-1]['originalFinished']=='1','Both cars must cross the finish'
    if hasTruck:assert rows[-1]['truckFinished']=='1','Truck must cross the finish'
    count=len(rows);duration=count/30;t=np.arange(round(duration*RATE))/RATE;frameTimes=np.arange(count)/30
    mix=np.zeros((len(t),2));sources=[]
    field=lambda key:np.array([float(r[key]) for r in rows])
    cx,cz=field('cameraX'),field('cameraZ')
    mx=(field('safariX')+field('originalX'))*.5;mz=(field('safariZ')+field('originalZ'))*.5
    if hasTruck:mx=(mx*2+field('truckX'))/3;mz=(mz*2+field('truckZ'))/3
    fx,fz=mx-cx,mz-cz;length=np.maximum(np.hypot(fx,fz),.01);fx/=length;fz/=length
    voices=[('safari','safari'),('original','cinder')]+([('truck','cinder')] if hasTruck else [])
    for prefix,filePrefix in voices:
        dx,dz=field(prefix+'X')-cx,field(prefix+'Z')-cz
        distance=np.maximum(np.hypot(dx,dz),.1)
        pan=np.clip(2*(dx*fz-dz*fx)/distance,-.75,.75)
        attenuation=.75/(1+(distance/20)**2)
        leftGain=np.interp(t,frameTimes,np.cos((pan+1)*np.pi/4)*attenuation)
        rightGain=np.interp(t,frameTimes,np.sin((pan+1)*np.pi/4)*attenuation)
        voice=np.zeros(len(t))
        for band,name in enumerate(('idle','mid','high')):
            source=ROOT/'showcase/assets'/f'{filePrefix}_exhaust_{name}.wav'
            with wave.open(str(source),'rb') as w:
                assert w.getframerate()==RATE and w.getsampwidth()==2 and w.getnchannels()==1
                sample=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float)/32768
            pitch=np.interp(t,frameTimes,field(f'{prefix}Pitch{band}'));gain=np.interp(t,frameTimes,field(f'{prefix}Gain{band}'))
            assert min(pitch)>0 and min(gain)>=0
            phase=np.mod(np.cumsum(pitch)-pitch+(.173*RATE if prefix=='truck' else 0),len(sample));index=np.floor(phase).astype(int);fraction=phase-index
            voice+=(sample[index]*(1-fraction)+sample[(index+1)%len(sample)]*fraction)*gain
            sources.append({'file':str(source.relative_to(ROOT)),'sha256':sha(source),'car':prefix,'band':band})
        mix[:,0]+=voice*leftGain;mix[:,1]+=voice*rightGain
    fade=round(.035*RATE);mix[:fade]*=np.linspace(0,1,fade)[:,None];mix[-fade:]*=np.linspace(1,0,fade)[:,None]
    audio=proof/'race-exhaust.wav';write_audio(audio,mix)
    before=measure(audio);gainDb=min(-18-before['lufs'],-3-before['truePeakDb']);mix*=10**(gainDb/20);write_audio(audio,mix)
    listing=proof/'concat.txt';listing.write_text(''.join(f"file '{p.name}'\n" for p in clips))
    picture=proof/'native-picture.mp4';run(['ffmpeg','-nostdin','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(picture)],proof/'concat.log')
    run(['ffmpeg','-nostdin','-v','error','-y','-i',str(picture),'-i',str(audio),'-c:v','copy','-c:a','aac','-threads','2','-b:a','192k','-ar',str(RATE),'-movflags','+faststart','-shortest',str(output)],proof/'mux.log')
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]).stdout)
    v=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert v['width']==960 and v['height']==600 and v['avg_frame_rate']=='30/1' and int(v['nb_frames'])==count
    assert abs(float(probe['format']['duration'])-duration)<.05
    decoded=run(['ffmpeg','-nostdin','-v','error','-threads','2','-i',str(output),'-f','null','-'],proof/'decode.log');assert not decoded.stderr
    metrics=measure(output);assert metrics['truePeakDb']<0
    result={'picture':'Continuous 960x600 30fps native framebuffer race; no upscaling, interpolation or invented pictures.',
            'audio':'Reconstructed dual exhaust from native per-car controls, continuous sample phases and camera-relative stereo; not endpoint audio.',
            'staging':'Scripted two-lane AI race on capture-only 8.6m-wide road (same vertex/index count), with original buggy catch-up governor. Not a handling or speed benchmark. Existing rocks relocated beyond two-wide tyre corridor, same pool and matching colliders.',
            'frames':count,'seconds':duration,'minimumEnvelopeGapMetres':min(field('envelopeGap')),
            'safariFinishSeconds':float(rows[-1]['safariFinish']),'originalFinishSeconds':float(rows[-1]['originalFinish']),
            'continuity':'Second take warmup states exactly match all first-take states. No duplicated or omitted picture frames.',
            'binarySha256':binary,'safariAssetSha256':asset,'clips':records,'audioSources':sources,'movieGainDb':gainDb,
            'audioMeasurement':metrics,'fullDecodePassed':True,'outputSha256':sha(output),'bytes':output.stat().st_size,
            'truckAssetSha256':truckAsset,'scriptSha256':sha(Path(__file__)),'limits':['Native body centres are inside the logged framing bounds. Moving pixels are reviewed separately.','Human listening/handling acceptance and sustained real-time performance are not established.']}
    if hasTruck:
        result['minimumEnvelopeGapMetres']=min(float(r[k]) for r in rows for k in ('envelopeGap','safariTruckGap','originalTruckGap'))
        result['truckFinishSeconds']=float(rows[-1]['truckFinish'])
        result['audio']='Three exhaust voices reconstructed from per-vehicle runtime bands, continuous sample phases and camera-relative stereo; not endpoint audio.'
        result['staging']='Three-lane capture-only 13m road with shifted existing rocks, markers and grass, same instance/road vertex budgets. Independent scripted AI with catch-up governors; not a fair performance comparison.'
        result['truckMotion']='Mechanically repaired Baja v3: force-based2200kg seven-coordinate vertical ride, fixed-length wishbones and steel links, rigid rear axle with elastic bushes, telescopic dampers and rotating brake discs. Authored travel0.268–0.52m. Scripted planar motion; not complete coupled vehicle physics.'
        result['truckAudio']='Temporary adaptation of existing CC0 generic buggy engine loops with lower truck RPM mapping; not a recording of this truck.'
    result['audioCredits']=[json.loads((ROOT/'showcase/assets'/name).read_text(encoding='utf-8-sig')) for name in ('SAFARI-EXHAUST-SOURCE.json','EXHAUST-SOURCE.json')]
    (proof/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');(proof/'probe.json').write_text(json.dumps(probe,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('clips','audioSources','audioCredits')},indent=2))

if __name__=='__main__':main()
