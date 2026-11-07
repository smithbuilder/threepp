"""Bind two independent visual decisions to the exact frozen, checked car."""
from pathlib import Path
from decimal import Decimal
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--round', required=True)
args = parser.parse_args()
assert args.round.isdigit()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
folder = ROOT / 'build/la-catrina'
model = ROOT / 'showcase/assets/la-catrina.glb'
digest = sha(model)
manifest = read(model.with_suffix('.json'))
assert manifest['sha256'] == digest and manifest['bakedCavityShading']
assert sha(folder / ('round-' + args.round) / 'la-catrina.glb') == digest
for name, expected in manifest['sourceFiles'].items():
    assert sha(ROOT / 'scripts' / name) == expected
for name, field in [('asset-audit.json', 'assetSha256'), ('enclosure-audit.json', 'modelSha256')]:
    report = read(folder / name)
    assert report['status'] == 'PASS' and report[field] == digest
receipt_path = folder / ('round-' + args.round) / 'studio/receipt.json'
receipt = read(receipt_path)
assert receipt['modelSha256'] == digest and len(receipt['captures']) == 16
assert len({c['name'] for c in receipt['captures']}) == 16
for capture in receipt['captures']:
    assert sha(Path(capture['path'])) == capture['sha256']
reviews = []
identities = set()
for suffix in ('a', 'b'):
    path = folder / 'independent' / f'round-{args.round}-{suffix}.json'
    report = read(path)
    assert report['model_sha256'] == digest
    assert report['reference_sha256'] == receipt['referenceSha256']
    categories = report.get('categories', report.get('category_scores'))
    weights = [Decimal(str(c['weight'])) for c in categories]
    assert weights == list(map(Decimal, ['.25', '.20', '.20', '.20', '.15']))
    score = sum(Decimal(str(c['score'])) * w for c, w in zip(categories, weights))
    assert score == Decimal(str(report['weighted_score_unrounded']))
    assert score >= 8 and report['threshold_met'] is True
    identity = report.get('evaluator', report.get('reviewer'))
    assert identity and identity not in identities
    identities.add(identity)
    observed = {i['sha256'] for i in report['inspected_images']}
    assert all(c['sha256'] in observed for c in receipt['captures'])
    reviews.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'score': float(score)})
mechanical_path = folder / 'independent' / f'round-{args.round}-mechanical.json'
mechanical = read(mechanical_path)
assert mechanical['status'].startswith('PASS')
for name, expected in mechanical['results']['sourceHashes'].items():
    assert sha(ROOT / name) == expected, name
acceptance = {'threshold': 8, 'modelSha256': digest, 'reviews': reviews,
    'captureReceipt': {'path': receipt_path.relative_to(ROOT).as_posix(), 'sha256': sha(receipt_path)},
    'mechanicalReview': {'path': mechanical_path.relative_to(ROOT).as_posix(), 'sha256': sha(mechanical_path),
        'geometrySha256': manifest['geometrySha256'],
        'binding': 'Unchanged reviewed author sources exported to this geometry; baked shading does not move vertices. Review scope and limitations remain those in the report.'}}
target = folder / 'independent/accepted-model.json'
assert not target.exists(), 'Refusing to replace an existing acceptance decision.'
target.write_text(json.dumps(acceptance, indent=2) + '\n', encoding='utf-8')
print(json.dumps(acceptance, indent=2))
