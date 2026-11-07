"""Cheap local preflight; never starts a browser or substitutes for visual review."""
from pathlib import Path
import hashlib,json,sys

ROOT=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
try:
    source=json.loads((ROOT/'source-manifest.json').read_text())
    package=json.loads((ROOT/'source-package-manifest.json').read_text())
    assert source['status']==package['status']=='PASS'
    assert source['nativeFramesVerified']==1440 and source['durationSeconds']==48
    assert source['modelSha256']==package['modelSha256']
    assert sha(ROOT/'source-manifest.json')==package['sourceManifestSha256']
    assert sha(ROOT/'native-captures.json')==package['nativeManifestSha256']
    approval=json.loads((ROOT/'Source/review/accepted-model.json').read_text(encoding='utf-8-sig'))
    assert sha(ROOT/'Source/review/accepted-model.json')==source['approvalSha256']
    assert approval['threshold']==8 and approval['modelSha256'].lower()==source['modelSha256']
    assert len(package['reviews'])>=2 and len({r['sha256'] for r in package['reviews']})>=2
    for r in package['reviews']:
        p=(ROOT/r['file']).resolve();assert p.is_relative_to(ROOT/'Source/review') and sha(p)==r['sha256']
        review=json.loads(p.read_text(encoding='utf-8-sig'))
        assert review['weighted_score_unrounded']==r['score'] and r['score']>=8 and review['threshold_met'] is True
        assert review.get('model_sha256',review.get('modelSha256','')).lower()==source['modelSha256']
    assert len(source['clips'])==6
    for c in source['clips']:
        p=(ROOT/c['video']).resolve();assert p.is_relative_to(ROOT/'assets/video') and sha(p)==c['sha256']
    files=[ROOT/'index.html',ROOT/'edit-manifest.json']+list((ROOT/'compositions').glob('*.html'))
    files+= [p for p in (ROOT/'assets').rglob('*') if p.is_file()]
    records=[p.relative_to(ROOT).as_posix()+':'+sha(p) for p in sorted(files)]
    digest=hashlib.sha256('\n'.join(records).encode()).hexdigest()
    if '--require-checks' in sys.argv:
        for stage in ('check','snapshot'):
            receipt=json.loads((ROOT/f'proof/{stage}-execution.json').read_text(encoding='utf-8-sig'))
            assert receipt['status']=='PASS' and receipt['authoringSha256']==digest,'Repeat check/snapshots after composition or media changes'
    if '--require-preview' in sys.argv:
        receipt=json.loads((ROOT/'proof/preview-execution.json').read_text(encoding='utf-8-sig'))
        preview=json.loads((ROOT/'proof/preview-session.json').read_text(encoding='utf-8-sig'))
        assert receipt['status']=='PASS' and receipt['authoringSha256']==digest,'Repeat the bounded preview after composition or media changes'
        assert receipt['modelSha256']==source['modelSha256']
        assert preview['status']=='PASS' and preview['httpStatus']==200 and preview['stopped'] is True
        assert preview['cliVersion']=='0.9.19' and preview['browserGpu']=='software' and preview['openedHeadless'] is True
        assert sha(ROOT/preview['screenshot'])==preview['screenshotSha256'],'Preview screenshot changed after review'
    print(json.dumps({'status':'PASS','modelSha256':source['modelSha256'],'authoringSha256':digest,'nativeFramesVerified':1440}))
except (FileNotFoundError,KeyError,ValueError,AssertionError) as e:
    print('Film preflight is pending: two exact-model8/10 reviews, verified native sources and current checks are required. '+str(e),file=sys.stderr)
    raise SystemExit(1)
