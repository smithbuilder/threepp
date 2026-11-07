"""Capture a hash-bound neutral review set through the shared supervisor."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--round',required=True);args=parser.parse_args()
out=root/'build/la-catrina'/('round-'+args.round)/'studio';out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
asset=root/'showcase/assets/la-catrina.glb';asset_hash=sha(asset)
assert sha(root/'build/windows-gl/bin/Release/catrina-assets/la-catrina.glb')==asset_hash
shots=[('front',0,1),('side',1,1),('rear',2,1),('top',3,1),('front-detail',4,1),('rear-detail',5,1),('cabin',6,1),('trunk',2,2),('bay-detail',5,2),('hood-open',0,3),('front-suspension-service',4,3),('rear-suspension-service',5,3),('right-side',1,3),('wheel-detail',4,2),('front-corner-wheel-off',6,3),('rear-links-wheel-off',6,2)]
records=[]
for name,view,pose in shots:
    print('Reference view: '+name,flush=True)
    run=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File','Run-Evaluation.ps1','-Example','catrina_preview','-Capture','-Frames','1','-View',str(view),'-Scene',str(pose),'-Seconds','30'],cwd=root,capture_output=True,text=True,timeout=45)
    (out/(name+'-supervisor.log')).write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('Capture failed. No retry; inspect '+name+'-supervisor.log')
    line=next(l for l in run.stdout.splitlines() if l.startswith('Evaluation exited cleanly. Logs: '))
    session=Path(line.split('Logs: ',1)[1]);receipt=json.loads((session/'result.json').read_text(encoding='utf-8-sig'))
    assert receipt['exitCode']==0 and receipt['vehicleAssetSha256'].lower()==asset_hash
    assert not (session/'stderr.log').read_text().strip()
    target=out/(name+'.png');shutil.copy2(session/'capture.png',target)
    records.append(dict(name=name,path=str(target),sha256=sha(target),view=view,pose=pose,session=str(session),binarySha256=receipt['binarySha256'].lower()))
    (out/'receipt.json').write_text(json.dumps(dict(modelSha256=asset_hash,referenceSha256=sha(root/'docs/la-catrina/references/La-Catrina-Master.jpg'),captures=records),indent=2)+'\n')
print('PASS: '+str(len(shots))+' reference images bound to '+asset_hash,flush=True)
