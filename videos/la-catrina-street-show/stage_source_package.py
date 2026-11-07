"""Freeze review/native evidence only after full native-source verification passes."""
from pathlib import Path
import hashlib,json,re,shutil

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent.parent
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def verified_studio_receipt(captureReceipt,modelSha256):
    receipt=Path(captureReceipt['path'])
    receipt=(receipt if receipt.is_absolute() else REPO/receipt).resolve()
    assert receipt.is_relative_to(REPO/'build/la-catrina'),'Studio receipt is outside La Catrina evidence'
    assert sha(receipt)==captureReceipt['sha256'].lower(),'Accepted studio receipt hash changed'
    data=json.loads(receipt.read_text(encoding='utf-8-sig'))
    assert data['modelSha256'].lower()==modelSha256.lower(),'Studio images belong to a different model'
    assert len(data['captures'])==16,'Expected the complete16-image studio review set'
    seen=set();captures=[]
    for capture in data['captures']:
        name=capture['name']
        assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',name),'Unsafe studio capture name'
        assert name.casefold() not in seen,'Duplicate studio capture name'
        seen.add(name.casefold())
        path=Path(capture['path']);path=(path if path.is_absolute() else REPO/path).resolve()
        assert path.is_relative_to(receipt.parent) and path.suffix.lower()=='.png','Unexpected studio image location or format'
        assert sha(path)==capture['sha256'].lower(),f'Studio image hash changed: {name}'
        captures.append({'name':name,'path':path,'sha256':capture['sha256'].lower(),'destination':f'Source/review/studio/{name}.png'})
    return receipt,data,captures

def verified_mechanical_review(mechanicalReview,modelSha256):
    report=Path(mechanicalReview['path'])
    report=(report if report.is_absolute() else REPO/report).resolve()
    assert report.is_relative_to(REPO/'build/la-catrina/independent'),'Mechanical review is outside independent evidence'
    assert sha(report)==mechanicalReview['sha256'].lower(),'Accepted mechanical review hash changed'
    data=json.loads(report.read_text(encoding='utf-8-sig'))
    assert data['status'].startswith('PASS'),'Mechanical review did not pass its stated scope'
    assert mechanicalReview['binding'].strip(),'Missing source-to-geometry binding description'
    results=data['results']
    assert results['hashesUnchanged'] is True and results['sourceHashes']==results['sourceHashesAfter'],'Reviewed sources changed during the mechanical checks'
    assert results['sourceHashes'],'Mechanical review has no source identity'
    modelManifest=REPO/'showcase/assets/la-catrina.json'
    manifest=json.loads(modelManifest.read_text(encoding='utf-8-sig'))
    assert sha(modelManifest.with_suffix('.glb'))==modelSha256.lower(),'Current model differs from accepted model'
    assert manifest['sha256'].lower()==modelSha256.lower(),'Model manifest belongs to another model'
    assert manifest['geometrySha256'].lower()==mechanicalReview['geometrySha256'].lower(),'Mechanical geometry binding differs from the model manifest'
    assert manifest['sourceFiles'],'Model manifest has no author source identity'
    for name,expected in manifest['sourceFiles'].items():
        path=(REPO/'scripts'/name).resolve()
        assert path.is_relative_to(REPO/'scripts'),'Unexpected model author source path'
        assert sha(path)==expected.lower(),f'Model author source changed: {name}'
    for name,expected in results['sourceHashes'].items():
        path=(REPO/name).resolve()
        assert path.is_relative_to(REPO),'Mechanical source is outside the project'
        assert sha(path)==expected.lower(),f'Mechanically reviewed source changed: {name}'
        if path.parent==REPO/'scripts':
            assert manifest['sourceFiles'][path.name].lower()==expected.lower(),f'Mechanical/model source binding differs: {name}'
    markdown=report.with_suffix('.md')
    assert markdown.is_file() and markdown.read_text(encoding='utf-8-sig').strip(),'Missing readable mechanical review'
    reproducer=report.with_name(report.stem+'-check.py')
    declared=Path(data['reproducer']['script'])
    declared=(declared if declared.is_absolute() else REPO/declared).resolve()
    assert reproducer==declared,'Mechanical reproducer must retain its reviewed same-prefix filename'
    assert sha(reproducer)==data['reproducer']['scriptSha256'].lower(),'Mechanical reproducer hash changed'
    return report,markdown,reproducer,modelManifest,data

source=json.loads((ROOT/'source-manifest.json').read_text())
assert source['status']=='PASS' and source['nativeFramesVerified']==1440
accept=REPO/'build/la-catrina/independent/accepted-model.json'
assert sha(accept)==source['approvalSha256']
approval=json.loads(accept.read_text(encoding='utf-8-sig'))
assert approval['modelSha256'].lower()==source['modelSha256'].lower()
studioReceipt,studioData,studioCaptures=verified_studio_receipt(approval['captureReceipt'],source['modelSha256'])
mechanicalReport,mechanicalMarkdown,mechanicalScript,mechanicalManifest,mechanicalData=verified_mechanical_review(approval['mechanicalReview'],source['modelSha256'])
entries=[]
def copy(p,destination,expectedSha256=None):
    sourceHash=sha(p)
    if expectedSha256 is not None:assert sourceHash==expectedSha256.lower(),f'Source hash changed before copy: {p}'
    target=ROOT/destination;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    assert sha(target)==sourceHash,f'Copied evidence hash mismatch: {target}'
    entries.append({'file':destination,'sha256':sourceHash,'bytes':target.stat().st_size,'originalPath':str(p)})
copy(accept,'Source/review/accepted-model.json')
studioDestination='Source/review/studio/receipt.json'
copy(studioReceipt,studioDestination,approval['captureReceipt']['sha256'])
for capture in studioCaptures:copy(capture['path'],capture['destination'],capture['sha256'])
mechanicalDestinations={name:'Source/review/'+path.name for name,path in (('report',mechanicalReport),('markdown',mechanicalMarkdown),('script',mechanicalScript))}
copy(mechanicalReport,mechanicalDestinations['report'],approval['mechanicalReview']['sha256'])
copy(mechanicalMarkdown,mechanicalDestinations['markdown'])
copy(mechanicalScript,mechanicalDestinations['script'],mechanicalData['reproducer']['scriptSha256'])
modelManifestDestination='Source/review/accepted-model-manifest.json'
copy(mechanicalManifest,modelManifestDestination)
reviewEvidence=[]
for i,r in enumerate(source['independentReviews'],1):
    p=Path(r['path']);assert sha(p)==r['sha256']
    destination=f'Source/review/review-{i}.json';copy(p,destination,r['sha256'])
    markdown=p.with_suffix('.md')
    assert markdown.is_file() and markdown.read_text(encoding='utf-8-sig').strip(),f'Missing readable review counterpart: {markdown}'
    markdownDestination=f'Source/review/review-{i}.md';copy(markdown,markdownDestination)
    reviewEvidence.append({'file':destination,'sha256':r['sha256'],'score':r['score'],'markdownFile':markdownDestination,'markdownSha256':sha(ROOT/markdownDestination)})
native=json.loads((ROOT/'native-captures.json').read_text())
for c in native['clips']:
    session=Path(c['session'])
    for name in ('result.json','drive.json','drive.json.csv','stdout.log','stderr.log'):
        p=session/name
        if p.exists():copy(p,f'Source/native/{c["name"]}/{name}')
for relative in ('scripts/capture-catrina-film.py','showcase/suspension_playground.cpp','showcase/CatrinaRig.hpp','showcase/CatrinaHydraulics.hpp','showcase/CatrinaDimensions.hpp','Run-Evaluation.ps1','docs/la-catrina/REAL-WORLD-BASIS.md','docs/la-catrina/PHYSICS.md','docs/la-catrina/RIG.md','docs/la-catrina/FRAME-POCKETS.md'):
    p=REPO/relative
    if p.exists():copy(p,'Source/project/'+relative)
reference=REPO/'docs/la-catrina/references/La-Catrina-Master.jpg'
if reference.exists():copy(reference,'Source/reference/La-Catrina-Master.jpg',studioData['referenceSha256'])
studioEvidence={'receiptFile':studioDestination,'receiptSha256':approval['captureReceipt']['sha256'].lower(),'modelSha256':studioData['modelSha256'].lower(),'referenceSha256':studioData['referenceSha256'].lower(),'imageCount':len(studioCaptures),'images':[{'name':c['name'],'file':c['destination'],'sha256':c['sha256']} for c in studioCaptures],'everyImageHashVerifiedBeforeAndAfterCopy':True}
mechanicalEvidence={'file':mechanicalDestinations['report'],'sha256':sha(ROOT/mechanicalDestinations['report']),
    'markdownFile':mechanicalDestinations['markdown'],'markdownSha256':sha(ROOT/mechanicalDestinations['markdown']),
    'reproducerFile':mechanicalDestinations['script'],'reproducerSha256':sha(ROOT/mechanicalDestinations['script']),
    'modelManifestFile':modelManifestDestination,'modelManifestSha256':sha(ROOT/modelManifestDestination),
    'modelSha256':source['modelSha256'],'geometrySha256':approval['mechanicalReview']['geometrySha256'].lower(),
    'binding':approval['mechanicalReview']['binding'],'sourceHashes':mechanicalData['results']['sourceHashes'],
    'sourceHashesVerifiedAgainstCurrentFilesAndModelManifest':True,
    'reproducerContext':'Unmodified CPU reproducer. Run from the full engine checkout with the author sources, native pose CSV and prior review dependencies identified in the script/report; the editable film archive is not a standalone engine build.'}
result={'status':'PASS','modelSha256':source['modelSha256'],'sourceManifestSha256':sha(ROOT/'source-manifest.json'),'nativeManifestSha256':sha(ROOT/'native-captures.json'),'reviews':reviewEvidence,'studioReview':studioEvidence,'mechanicalReview':mechanicalEvidence,'entries':entries,'scope':'Editable native clips, music/action tracks and frozen provenance are self-contained. Full engine checkout and raw native PNG sequences are separately retained in the project, not duplicated here.'}
(ROOT/'source-package-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print('Staged verified review and native evidence: '+str(len(entries))+' files')
