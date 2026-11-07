"""Retain the exact model, authoring sources and checks behind one studio review."""
from pathlib import Path
import argparse, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--round', required=True)
args = parser.parse_args()
assert args.round.isdigit()
out = ROOT / 'build/la-catrina' / ('round-' + args.round)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
model = ROOT / 'showcase/assets/la-catrina.glb'
manifest = read(model.with_suffix('.json'))
assert manifest['sha256'] == sha(model)
studio = read(out / 'studio/receipt.json')
assert studio['modelSha256'] == sha(model) and len(studio['captures']) == 16
for capture in studio['captures']:
    assert sha(Path(capture['path'])) == capture['sha256']
for name, key in [('asset-audit.json', 'assetSha256'), ('enclosure-audit.json', 'modelSha256')]:
    audit = read(ROOT / 'build/la-catrina' / name)
    assert audit['status'] == 'PASS' and audit[key] == sha(model)
files = ['showcase/assets/la-catrina.glb', 'showcase/assets/la-catrina.json',
         'showcase/CatrinaRig.hpp', 'showcase/catrina_preview.cpp',
         'docs/la-catrina/bakes/vertex-ao.npz', 'docs/la-catrina/bakes/vertex-ao.json',
         'build/la-catrina/asset-audit.json', 'build/la-catrina/enclosure-audit.json',
         'build/la-catrina/preview-audit.json', 'build/suspension-playground/latest-audit.json',
         'build/la-catrina/physics-comparison.json']
files += ['scripts/' + name for name in manifest['sourceFiles']]
records = []
for relative in files:
    source = ROOT / relative
    if relative.startswith('scripts/'):
        assert sha(source) == manifest['sourceFiles'][source.name]
    target = out / ('sources' if relative.startswith('scripts/') else '') / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), 'Refusing to replace frozen evidence: ' + str(target)
    shutil.copy2(source, target)
    assert sha(target) == sha(source)
    records.append({'source': relative, 'archive': target.relative_to(ROOT).as_posix(), 'sha256': sha(target)})
(out / 'archive.json').write_text(json.dumps({'modelSha256': sha(model),
    'status': 'Frozen candidate; visual decision is in the separate independent reports.',
    'files': records}, indent=2) + '\n', encoding='utf-8')
print('Frozen exact review model and ' + str(len(records)) + ' evidence files.')
