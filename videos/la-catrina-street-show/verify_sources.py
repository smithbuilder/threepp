"""Bind every encoded frame to accepted model, independent reviews and native receipts."""
from pathlib import Path
import csv,hashlib,json,math,subprocess,sys

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent.parent
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def verify_motion(session,frames,warmup):
    """Read actual native state, retaining only post-warmup film samples as metrics.

    Contact evidence is the physics solver's footprint query, not a pixel-space
    clearance test. A zero-load tire alone does not establish flight; a specific
    missing tire is inferred only when all remaining contacts carry positive load.
    """
    summaryPath=session/'drive.json';csvPath=session/'drive.json.csv'
    summary=json.loads(summaryPath.read_text(encoding='utf-8-sig'))
    assert summary['physicsHz']==240,(session,'Unexpected physics frequency')
    assert summary['discardedBacklogs']==0,(session,'Discarded physics backlog')
    expectedSeconds=(frames+warmup)/30
    # The native counter accumulates240Hz steps in float32. Five milliseconds
    # covers the observed accumulation rounding while remaining below one frame.
    tolerance=.005;actualSeconds=float(summary['simulatedSeconds'])
    assert math.isfinite(actualSeconds) and abs(actualSeconds-expectedSeconds)<=tolerance,(session,'Simulation time mismatch',actualSeconds,expectedSeconds)
    with csvPath.open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    assert len(rows)==frames+warmup,(session,'Telemetry row count mismatch')
    for i,row in enumerate(rows):
        assert int(row['frame'])==i,(session,'Missing or repeated telemetry frame',i)
        assert all(math.isfinite(float(v)) for v in row.values()),(session,'Non-finite telemetry',i)
        assert abs(float(row['t'])-(i+1)/30)<=tolerance,(session,'Telemetry time drift',i)
        assert int(row['contacts']) in range(5),(session,'Invalid contact count',i)
    assert abs(float(rows[-1]['t'])-actualSeconds)<=.0001,(session,'Summary and CSV time disagree')
    displayed=rows[warmup:];assert len(displayed)==frames
    loads=[[float(row[k]) for k in ('flLoad','frLoad','rlLoad','rrLoad')] for row in displayed]
    contacts=[int(row['contacts']) for row in displayed]
    def intervals(flags):
        result=[];start=None
        for i,flag in enumerate(flags+[False]):
            if flag and start is None:start=i
            elif not flag and start is not None:
                result.append({'firstClipFrame':start,'lastClipFrame':i-1,'firstNativeFrame':warmup+start,'lastNativeFrame':warmup+i-1,'startSeconds':start/30,'durationSeconds':(i-start)/30});start=None
        return result
    # Positive>1N proves support; ≤1e-6N is serialized zero, not a near-zero load.
    zero=lambda value:abs(value)<=1e-6
    frontPair=[n==2 and zero(l[0]) and zero(l[1]) and l[2]>1 and l[3]>1 for n,l in zip(contacts,loads)]
    leftFront=[n==3 and zero(l[0]) and all(v>1 for v in l[1:]) for n,l in zip(contacts,loads)]
    rightFront=[n==3 and zero(l[1]) and all(l[j]>1 for j in (0,2,3)) for n,l in zip(contacts,loads)]
    flight={'zeroContacts':intervals([n==0 for n in contacts]),'frontPairNoContactWithRearSupport':intervals(frontPair),'leftFrontNoContactWithThreeLoadedTires':intervals(leftFront),'rightFrontNoContactWithThreeLoadedTires':intervals(rightFront),'fourContacts':intervals([n==4 for n in contacts])}
    positions=[[float(row[k]) for k in ('x','y','z')] for row in displayed]
    path=sum(math.dist(a,b) for a,b in zip(positions,positions[1:]))
    modes={};speeds=[float(row['speed']) for row in displayed]
    for row in displayed:modes[row['hydraulicMode']]=modes.get(row['hydraulicMode'],0)+1
    return {'summarySha256':sha(summaryPath),'csvSha256':sha(csvPath),'physicsHz':240,'discardedBacklogs':0,'simulatedSeconds':actualSeconds,'expectedSimulatedSeconds':expectedSeconds,'timeToleranceSeconds':tolerance,'totalTelemetryRows':len(rows),'warmupFramesExcluded':warmup,'displayedFrames':frames,'postWarmup':{'contactFrameCounts':{str(n):contacts.count(n) for n in range(5)},'hydraulicModeFrameCounts':modes,'pathLengthMeters':path,'speedMetersPerSecond':{'minimum':min(speeds),'maximum':max(speeds)},'chassisOriginHeightMeters':{'minimum':min(p[1] for p in positions),'maximum':max(p[1] for p in positions)},'wheelLoadRangesNewtons':{name:{'minimum':min(l[i] for l in loads),'maximum':max(l[i] for l in loads)} for i,name in enumerate(('FL','FR','RL','RR'))},'contactIntervals':flight},'interpretation':'30fps samples of the240Hz solver. Per-tire noncontact is inferred only from the total contact count plus positive support loads on every other tire. Visual tire clearance, linkage articulation and continuous motion still require frame review.'}

def verify_motion_task(name,motion):
    """Require the requested action in verified post-warmup samples.

    Durations accumulate qualifying30fps samples across the clip. A recovery
    sample must follow an observed front-pair lift, not merely precede it.
    These fixed modest bounds do not replace visual clearance/motion review.
    """
    assert name in ('reveal','hop','wheel','left','right','exit'),'Unexpected film shot'
    post=motion['postWarmup'];contacts=post['contactIntervals']
    observed={'pathLengthMeters':post['pathLengthMeters']}
    requirements={'pathLengthMetersGreaterThan':1.0}
    failures=[]
    if not observed['pathLengthMeters']>1:failures.append('Post-warmup path must exceed1 metre')
    if name in ('hop','wheel','left','right'):
        key={'hop':'frontPairNoContactWithRearSupport','wheel':'frontPairNoContactWithRearSupport',
             'left':'leftFrontNoContactWithThreeLoadedTires','right':'rightFrontNoContactWithThreeLoadedTires'}[name]
        minimumFrames=9 if name in ('hop','wheel') else 30
        ranges=contacts[key]
        sampleFrames=sum(r['lastClipFrame']-r['firstClipFrame']+1 for r in ranges)
        observed.update(contactCondition=key,qualifyingFrames=sampleFrames,qualifyingSeconds=sampleFrames/30,
                        longestQualifyingIntervalSeconds=max((r['durationSeconds'] for r in ranges),default=0))
        requirements.update(contactCondition=key,minimumQualifyingFrames=minimumFrames,minimumQualifyingSeconds=minimumFrames/30)
        if sampleFrames<minimumFrames:failures.append(f'{key} requires at least{minimumFrames/30:.2f} seconds of qualifying samples')
        if name in ('hop','wheel'):
            recoveryFrames=0
            if ranges:
                after=ranges[0]['lastClipFrame']+1
                recoveryFrames=sum(max(0,r['lastClipFrame']-max(r['firstClipFrame'],after)+1) for r in contacts['fourContacts'])
            observed['fourContactRecoveryFramesAfterLift']=recoveryFrames
            requirements['minimumFourContactRecoveryFramesAfterLift']=1
            if recoveryFrames<1:failures.append('At least one four-contact recovery sample must follow the front-pair lift')
    assert not failures,(name,'Motion task gate failed; investigate the capture and report the result rather than lowering these bounds.',failures,observed)
    return {'status':'PASS','requirements':requirements,'observed':observed,
            'interpretation':'Cumulative post-warmup contact-state samples, with positively loaded support tires for each inferred missing tire. Visual tire clearance and continuous action still require review; zero wheel load alone is not flight evidence.'}

approvalPath=REPO/'build/la-catrina/independent/accepted-model.json'
approval=json.loads(approvalPath.read_text(encoding='utf-8-sig'))
expected=approval['modelSha256'].lower()
assert approval['threshold']==8 and len(approval['reviews'])>=2
reviews=[]
for r in approval['reviews']:
    p=Path(r['path']);p=p if p.is_absolute() else REPO/p
    assert p.resolve().is_relative_to(REPO/'build/la-catrina/independent')
    actual=json.loads(p.read_text(encoding='utf-8-sig'))
    assert sha(p)==r['sha256'] and r['score']>=8
    assert actual['weighted_score_unrounded']==r['score'] and actual['threshold_met'] is True
    assert actual.get('model_sha256',actual.get('modelSha256','')).lower()==expected
    reviews.append({'path':str(p),'sha256':sha(p),'score':r['score']})
assert len({r['sha256'] for r in reviews})>=2,'Two distinct review records are required'
assert sha(REPO/'showcase/assets/la-catrina.glb')==expected
manifest=json.loads((ROOT/'native-captures.json').read_text(encoding='utf-8-sig'))
edit=json.loads((ROOT/'edit-manifest.json').read_text());byname={c['name']:c for c in manifest['clips']}
assert manifest['modelSha256'].lower()==expected
checked=[];framesChecked=0
for scene in edit['scenes']:
    c=byname[scene['id']];p=ROOT/c['video'];session=Path(c['session']).resolve()
    assert p.resolve().is_relative_to(ROOT/'assets/video') and session.is_relative_to(REPO/'build/sessions')
    assert sha(p)==c['sha256'] and c['modelSha256'].lower()==expected
    receipt=json.loads((session/'result.json').read_text(encoding='utf-8-sig'))
    assert receipt['exitCode']==0 and receipt['sequence'] and receipt['requestedFrames']==c['frames']
    assert receipt['vehicleAssetSha256'].lower()==expected and receipt['binarySha256'].lower()==c['binarySha256'].lower()
    assert receipt['example']=='suspension_playground' and receipt['vehicle']=='catrina' and receipt['world']=='city'
    assert receipt['cleanCapture'] is True and receipt['playbackScale']==1
    assert receipt['hydraulics']==c['mode'],(scene['id'],'Hydraulic mode differs from capture plan')
    assert receipt['rightCamera'] is c['rightCamera'],(scene['id'],'Camera side differs from capture plan')
    assert receipt['warmupFrames']==c['warmupFrames'],(scene['id'],'Warmup differs from capture plan')
    assert receipt['view']==c['view'] and receipt['scene']==c['scene'],(scene['id'],'View or start station differs from capture plan')
    assert (receipt['renderWidth'],receipt['renderHeight'])==(960,600)
    assert not (session/'stderr.log').read_text().strip()
    motion=verify_motion(session,c['frames'],c['warmupFrames'])
    motion['taskGate']=verify_motion_task(scene['id'],motion)
    recorded={x['file']:x['sha256'] for x in c['frameHashes']}
    pictures=sorted((session/'frames').glob('frame_*.png'))
    assert len(pictures)==len(recorded)==c['frames']==round(scene['duration']*30)
    for i,picture in enumerate(pictures):
        assert int(picture.stem.split('_')[-1])==i and sha(picture)==recorded[picture.name]
    aggregate=hashlib.sha256('\n'.join(p.name+':'+recorded[p.name] for p in pictures).encode()).hexdigest()
    assert aggregate==c['sourceFramesSha256']
    distinct=len(set(recorded.values()));assert distinct>=c['frames']*.8,(scene['id'],distinct)
    framesChecked+=len(pictures)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],text=True))
    v=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (v['width'],v['height'])==(960,600) and v['avg_frame_rate']=='30/1' and int(v['nb_frames'])==c['frames']
    assert abs(float(probe['format']['duration'])-scene['duration'])<.002
    checked.append({'name':scene['id'],'video':c['video'],'sha256':c['sha256'],'frames':c['frames'],'distinctNativeFrames':distinct,'sourceSession':str(session),'modelSha256':expected,'binarySha256':c['binarySha256'],'everyNativePngHashVerified':True,'sourceReceiptSha256':sha(session/'result.json'),'captureProfile':{'hydraulics':receipt['hydraulics'],'rightCamera':receipt['rightCamera'],'warmupFrames':receipt['warmupFrames'],'view':receipt['view'],'scene':receipt['scene']},'motionTelemetry':motion})
assert framesChecked==1440 and len(checked)==6
result={'status':'PASS','modelSha256':expected,'approvalSha256':sha(approvalPath),'independentReviews':reviews,'durationSeconds':48,'width':960,'height':600,'fps':30,'nativeFramesVerified':framesChecked,'clips':checked,'mediaTreatment':'Full native frames at1x, no crop/upscale/interpolation/grade. Engine and pump sound are editorial reconstruction from credited recordings.'}
(ROOT/'source-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
subprocess.run([sys.executable,str(ROOT/'stage_source_package.py')],check=True)
print(json.dumps({'status':'PASS','clips':len(checked),'nativeFramesVerified':framesChecked,'modelSha256':expected},indent=2))
