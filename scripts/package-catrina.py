"""Package La Catrina model, editable authoring source, and verified receipts."""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, time, zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/la-catrina'
LIB = ROOT / 'asset-library/models/la-catrina'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))

model = LIB / 'la-catrina.glb'
physics = read(ROOT / 'build/suspension-playground/latest-audit.json')
session = Path(physics['session'])
assert read(session / 'physics-audit/result.json')['status'] == 'PASS'
assert read(session / 'physics-audit/catrina-rig-audit.json')['status'] == 'PASS'
binary = ROOT / 'build/windows-gl/bin/Release/suspension_playground.exe'
assert sha(binary) == physics['binarySha256'].lower()
assert sha(model) == sha(ROOT / 'showcase/assets/la-catrina.glb')
assert sha(model) == sha(ROOT / 'build/windows-gl/bin/Release/playground-assets/la-catrina.glb')
assert read(session/'result.json')['playgroundAssetSha256']['la-catrina.glb'].lower()==sha(model)
acceptance=read(OUT/'independent/accepted-model.json')
assert acceptance['threshold']==8 and acceptance['modelSha256']==sha(model)
assert len(acceptance['reviews'])>=2
assert len({review['path'] for review in acceptance['reviews']})>=2
for review in acceptance['reviews']:
    proof=ROOT/review['path'];report=read(proof)
    assert sha(proof)==review['sha256'] and report['model_sha256']==sha(model)
    assert report['threshold_met'] is True and report['weighted_score_unrounded']>=8
    assert report['weighted_score_unrounded']==review['score']
assert read(OUT/'asset-audit.json')['assetSha256']==sha(model)
assert read(OUT/'enclosure-audit.json')['modelSha256']==sha(model)
assert read(OUT/'asset-audit.json')['status']=='PASS'
assert read(OUT/'enclosure-audit.json')['status']=='PASS'
studio_path=ROOT/acceptance['captureReceipt']['path']
assert sha(studio_path)==acceptance['captureReceipt']['sha256']
studio=read(studio_path)
assert studio['modelSha256']==sha(model) and len(studio['captures'])==16

entries = []
def add(path, name): entries.append((path, 'La-Catrina/' + name))
for name in read(LIB/'asset.json')['files']:
    path=LIB/name
    assert path.resolve().parent==LIB.resolve() and path.is_file()
    add(path, 'Model/' + path.name)
for name in ('catrina_generate.py', 'catrina_art.py', 'catrina_hardware.py', 'catrina_frame_pockets.py', 'catrina_reference_paint.py', 'catrina_ao.py', 'catrina_audit.py', 'catrina_enclosure_audit.py', 'baja427_generate.py'):
    add(ROOT / 'scripts' / name, 'Source/scripts/' + name)
add(ROOT / 'docs/la-catrina/references/La-Catrina-Master.jpg', 'Source/docs/la-catrina/references/La-Catrina-Master.jpg')
for path in (ROOT/'docs/la-catrina/bakes').glob('vertex-ao.*'):
    add(path,'Source/docs/la-catrina/bakes/'+path.name)
for name in ('CatrinaRig.hpp', 'CatrinaHydraulics.hpp', 'CatrinaDimensions.hpp',
             'PlaygroundPhysics.hpp', 'PlaygroundVehicles.hpp', 'PlaygroundAudit.hpp'):
    add(ROOT / 'showcase' / name, 'Engine-adapter/' + name)
add(ROOT / 'LA-CATRINA.md', 'README.md')
add(ROOT / 'docs/la-catrina/HANDOFF.md', 'Review/HANDOFF.md')
for name in ('MODEL.md', 'PHYSICS.md', 'RIG.md', 'FRAME-POCKETS.md', 'MOTION-REVIEW.md', 'ART-REVISION.md', 'REAL-WORLD-BASIS.md', 'REFERENCE-PAINT.md'):
    add(ROOT / 'docs/la-catrina' / name, 'Review/' + name)
add(OUT / 'asset-audit.json', 'Review/asset-audit.json')
add(OUT / 'enclosure-audit.json', 'Review/enclosure-audit.json')
add(OUT / 'research.json', 'Review/research.json')
add(OUT / 'native-review.json', 'Review/native-review.json')
add(OUT / 'independent/accepted-model.json', 'Review/accepted-model.json')
add(OUT / 'physics-comparison.json', 'Review/physics-comparison.json')
for name in ('result.json', 'catrina-rig-audit.json', 'checks.csv', 'catrina-hydraulics.csv'):
    add(session / 'physics-audit' / name, 'Review/' + name)
add(studio_path,'Review/studio-receipt.json')
for capture in studio['captures']:
    path=Path(capture['path'])
    assert sha(path)==capture['sha256']
    assert Path(capture['name']).name==capture['name']
    add(path,'Review/Studio/'+capture['name']+'.png')
for path in sorted((OUT / 'independent').glob('*')):
    if path.is_file(): add(path, 'Review/Independent/' + path.name)

# The GLB must be reproducible from exactly the authoring source in this pack.
fresh = OUT / 'rebuild' / str(time.time_ns())
for path, name in entries:
    prefix = 'La-Catrina/Source/'
    if name.startswith(prefix):
        target = fresh / name[len(prefix):]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
for name in ('catrina_generate.py', 'catrina_audit.py'):
    result = subprocess.run([sys.executable, '-X', 'utf8', str(fresh / 'scripts' / name)],
                            cwd=fresh, capture_output=True, text=True)
    if result.returncode: raise RuntimeError(result.stdout + result.stderr)
assert sha(fresh / 'showcase/assets/la-catrina.glb') == sha(model)
rebuild = OUT / 'source-rebuild.json'
rebuild.write_text(json.dumps({'status': 'PASS', 'modelSha256': sha(model),
    'method': 'Regenerated and audited from the exact packaged sources in a fresh directory.'}, indent=2)+'\n')
add(rebuild, 'Review/source-rebuild.json')
archive = OUT / 'La-Catrina-Modular.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for path, name in entries: z.write(path, name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for path, name in entries: assert hashlib.sha256(z.read(name)).hexdigest() == sha(path)
receipt = {'status': 'PASS', 'modelSha256': sha(model), 'binarySha256': sha(binary),
    'archive': str(archive.relative_to(ROOT)), 'archiveSha256': sha(archive),
    'archiveBytes': archive.stat().st_size, 'archiveFiles': len(entries),
    'physicsChecks': physics['checks'], 'physicsSession': str(session),
    'sourceRebuild': 'PASS', 'limitations': [
        'Human handling and long-session acceptance remain unverified; independent visual scores are recorded separately.',
        'Raycast tyre forces and visual linkage solve are not a full multibody vehicle.',
        'Native captures retain the existing 960x600 graphics budget.']}
(OUT / 'delivery-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
