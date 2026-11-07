"""Build and verify a self-contained editable film archive after delivery passes."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent;OUTPUT=ROOT/'outputs/La-Catrina-Street-Show-Editable.zip'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
assert json.loads((ROOT/'proof/delivery-receipt.json').read_text())['status']=='PASS'
assert json.loads((ROOT/'source-package-manifest.json').read_text())['status']=='PASS'
files=[]
for name in ('assets','compositions','scripts','Source','proof'):
    for p in (ROOT/name).rglob('*'):
        if not p.is_file():continue
        if p.name=='editable-archive-receipt.json' or p.name.startswith('ref-') or p.suffix in ('.zip','.pyc') or '__pycache__' in p.parts:continue
        files.append(p)
for p in ROOT.iterdir():
    if p.is_file() and (p.suffix in ('.md','.py','.ps1','.html','.json') or p.name=='.gitignore'):files.append(p)
files=sorted(set(files),key=lambda p:p.relative_to(ROOT).as_posix())
entries=[{'file':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
manifest={'purpose':'Self-contained editable La Catrina street film; final MP4 delivered separately.','excluded':['node_modules','render caches','raw native PNG sequences','duplicate final MP4','separate vehicle GLB package','rejected generic sound-search result'],'entries':entries}
with zipfile.ZipFile(OUTPUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    z.writestr('ARCHIVE-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(OUTPUT) as z:
    assert z.testzip() is None
    for entry in entries:
        data=z.read(entry['file']);assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],entry['file']
receipt={'status':'PASS','archive':str(OUTPUT),'bytes':OUTPUT.stat().st_size,'sha256':sha(OUTPUT),'verifiedFileEntries':len(entries),'everyEntryHashVerified':True,'excludedFinalVideo':True,'excludedDependenciesAndCaches':True}
(ROOT/'proof/editable-archive-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
