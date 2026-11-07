"""Capture the independently accepted car using the actual shared driving simulation.
No native launches outside the existing signed, bounded supervisor.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT/'videos/la-catrina-street-show'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
model=ROOT/'showcase/assets/la-catrina.glb';accepted=json.loads((ROOT/'build/la-catrina/independent/accepted-model.json').read_text())
assert accepted['modelSha256']==sha(model) and len(accepted['reviews'])>=2
assert accepted['threshold']==8 and len({r['path'] for r in accepted['reviews']})>=2
for audit,key in [('asset-audit.json','assetSha256'),('enclosure-audit.json','modelSha256')]:
    checked=json.loads((ROOT/'build/la-catrina'/audit).read_text(encoding='utf-8-sig'))
    assert checked['status']=='PASS' and checked[key]==sha(model)
for review in accepted['reviews']:
    assert review['score']>=8 and sha(ROOT/review['path'])==review['sha256']
    report=json.loads((ROOT/review['path']).read_text(encoding='utf-8-sig'))
    assert report['model_sha256'].lower()==sha(model)
    assert report['threshold_met'] and report['weighted_score_unrounded']>=8
    assert report['weighted_score_unrounded']==review['score']
assert sha(ROOT/'build/windows-gl/bin/Release/playground-assets/la-catrina.glb')==sha(model)
shots=[('reveal',2,3,'cruise',180,60,False),('hop',1,1,'hop',300,60,False),('wheel',4,1,'hop',150,60,False),('left',1,2,'three-left',240,90,False),('right',1,1,'three-right',240,90,True),('exit',0,2,'cruise',330,60,False)]
records=[];(PROJECT/'assets/video').mkdir(parents=True,exist_ok=True);(PROJECT/'proof').mkdir(exist_ok=True)
for name,view,scene,mode,count,warmup,right in shots:
    print('Recording '+name+' / '+str(count)+' frames',flush=True)
    cmd=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File','Run-Evaluation.ps1','-Example','suspension_playground','-World','city','-Vehicle','catrina','-Sequence','-Frames',str(count),'-WarmupFrames',str(warmup),'-View',str(view),'-Scene',str(scene),'-Hydraulics',mode,'-AutoDrive','-CleanCapture','-Seconds','90']
    if right:cmd.append('-RightCamera')
    run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=105)
    (PROJECT/'proof'/f'{name}-supervisor.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('Native capture failed; no retry. Inspect '+name+'-supervisor.log')
    line=next(l for l in run.stdout.splitlines() if l.startswith('Evaluation exited cleanly. Logs: '));session=Path(line.split('Logs: ',1)[1])
    result=json.loads((session/'result.json').read_text(encoding='utf-8-sig'))
    assert result['exitCode']==0 and result['renderWidth']==960 and result['renderHeight']==600 and result['vehicleAssetSha256'].lower()==sha(model)
    assert result['cleanCapture'] and not (session/'stderr.log').read_text().strip()
    images=sorted((session/'frames').glob('frame_*.png'));assert len(images)==count
    hashes=[dict(file=p.name,sha256=sha(p)) for p in images];digest=hashlib.sha256('\n'.join(p['file']+':'+p['sha256'] for p in hashes).encode()).hexdigest()
    target=PROJECT/'assets/video'/f'{name}.mp4'
    command=['ffmpeg','-y','-hide_banner','-loglevel','warning','-framerate','30','-start_number','0','-i',str(session/'frames/frame_%05d.png'),'-frames:v',str(count),'-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p','-c:v','libx264','-preset','medium','-crf','17','-threads','2','-an','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',str(target)]
    with (PROJECT/'proof'/f'{name}-encode.log').open('w') as log:subprocess.run(command,stdout=log,stderr=log,check=True,timeout=90)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(target)],text=True));video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert video['width']==960 and video['height']==600 and int(video['nb_read_frames'])==count and video['avg_frame_rate']=='30/1'
    records.append(dict(name=name,video=target.relative_to(PROJECT).as_posix(),session=str(session),view=view,scene=scene,mode=mode,rightCamera=right,warmupFrames=warmup,frames=count,fps=30,width=960,height=600,duration=count/30,modelSha256=sha(model),binarySha256=result['binarySha256'].lower(),sourceFramesSha256=digest,frameHashes=hashes,sha256=sha(target),motion=str(session/'drive.json.csv'),description='Native shared Bullet vehicle physics; hydraulic preload, wheel contact and rigid visual linkage; normal 1x speed'))
    (PROJECT/'native-captures.json').write_text(json.dumps(dict(modelSha256=sha(model),clips=records,sourceFrameHashMethod='SHA256 of newline-joined filename:SHA256 in filename order',limits=dict(width=960,height=600,fpsMaximum=30,shadowMap=512,jobGiB=2,sequential=True),nativeSource='showcase/suspension_playground.cpp'),indent=2)+'\n')
    print('Ready '+name+' : '+str(session),flush=True)
assert sum(r['frames'] for r in records)==1440
print('PASS: six actual driving clips / 48 seconds',flush=True)
